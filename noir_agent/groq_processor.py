"""Interface to the Groq LLM for building ApiCollection objects."""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Callable, Dict, Iterable, List

from groq import Groq

from .models import ApiCollection, NoirEndpoint
from .schema import API_COLLECTION_SCHEMA

LOGGER = logging.getLogger(__name__)
MAX_REQUEST_CHARS = 12_000


class GroqError(RuntimeError):
    """Raised when the Groq API fails."""


def build_api_collection(base_url: str, noir_endpoints: List[NoirEndpoint], route_files: List[Dict[str, str]]) -> ApiCollection:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)

    system_msg = {
        "role": "system",
        "content": (
            "You are an API architect. Merge Noir endpoints with the provided route files, "
            "infer missing endpoints, and respond ONLY with valid JSON following the schema."
        ),
    }

    payloads = _prepare_payloads(base_url, noir_endpoints, route_files)

    collections: List[ApiCollection] = []
    for index, payload in enumerate(payloads, start=1):
        user_msg = {"role": "user", "content": json.dumps(payload, default=lambda o: o.dict(by_alias=True))}

        LOGGER.info(
            "Requesting Groq API to synthesize ApiCollection (chunk %d/%d)",
            index,
            len(payloads),
        )
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[system_msg, user_msg],
            temperature=0.2,
            max_completion_tokens=8192,
            top_p=1,
            reasoning_effort="medium",
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "api_collection",
                    "schema": API_COLLECTION_SCHEMA,
                    "strict": True,
                },
            },
            stream=False,
        )

        content = response.choices[0].message.content  # type: ignore[index]
        if not content:
            raise GroqError("Groq response was empty")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            LOGGER.error("Groq returned invalid JSON: %s", content)
            raise GroqError("Groq returned invalid JSON") from exc

        try:
            collection = ApiCollection(**data)
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.error("Groq JSON did not match ApiCollection: %s", data)
            raise GroqError("Groq JSON failed validation") from exc

        collections.append(collection)

    return _merge_collections(collections)


def _serialize_endpoints(endpoints: Iterable[NoirEndpoint]) -> List[Dict[str, Any]]:
    """Convert NoirEndpoint models into dicts for JSON serialization."""

    return [endpoint.dict(by_alias=True) for endpoint in endpoints]


def _chunk_list_by_size(items: List[Any], size_builder: Callable[[List[Any]], int], max_chars: int) -> List[List[Any]]:
    """Split a list into chunks whose serialized size stays under max_chars."""

    chunks: List[List[Any]] = []
    current: List[Any] = []
    for item in items:
        candidate = current + [item]
        if size_builder(candidate) <= max_chars:
            current = candidate
            continue

        if not current:
            # Even the single item is too large; force it into its own chunk to avoid
            # infinite loops and let the API return a clearer error.
            chunks.append([item])
            current = []
            continue

        chunks.append(current)
        current = [item]

    if current:
        chunks.append(current)

    return chunks


def _prepare_payloads(base_url: str, noir_endpoints: List[NoirEndpoint], route_files: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """Create Groq request payloads small enough to avoid request size errors."""

    base_payload = {"baseUrl": base_url}

    def endpoint_size(chunk: Iterable[NoirEndpoint]) -> int:
        payload = {**base_payload, "noirEndpoints": _serialize_endpoints(chunk), "routeFiles": []}
        return len(json.dumps(payload))

    def route_size(endpoint_chunk: Iterable[NoirEndpoint], route_chunk: Iterable[Dict[str, str]]) -> int:
        payload = {
            **base_payload,
            "noirEndpoints": _serialize_endpoints(endpoint_chunk),
            "routeFiles": list(route_chunk),
        }
        return len(json.dumps(payload))

    endpoint_chunks = _chunk_list_by_size(noir_endpoints, endpoint_size, MAX_REQUEST_CHARS)
    # Ensure we still send the route files to Groq even when Noir found no endpoints.
    if not endpoint_chunks:
        endpoint_chunks = [[]]

    payloads: List[Dict[str, Any]] = []
    for endpoint_chunk in endpoint_chunks:
        route_chunks = _chunk_list_by_size(
            route_files,
            lambda chunk: route_size(endpoint_chunk, chunk),
            MAX_REQUEST_CHARS,
        ) or [[]]

        for route_chunk in route_chunks:
            payloads.append(
                {
                    **base_payload,
                    "noirEndpoints": endpoint_chunk,
                    "routeFiles": route_chunk,
                }
            )

    return payloads


def _merge_collections(collections: List[ApiCollection]) -> ApiCollection:
    """Merge multiple ApiCollections into a single consolidated collection."""

    if not collections:
        raise GroqError("Groq did not return any collections")

    base = collections[0]
    merged_endpoints = []
    seen = set()

    for collection in collections:
        if collection.baseUrl != base.baseUrl:
            raise GroqError("Groq returned collections with mismatched base URLs")

        for endpoint in collection.endpoints:
            key = (endpoint.method.upper(), endpoint.path)
            if key in seen:
                continue
            seen.add(key)
            merged_endpoints.append(endpoint)

    return ApiCollection(
        title=base.title,
        version=base.version,
        baseUrl=base.baseUrl,
        endpoints=merged_endpoints,
    )
