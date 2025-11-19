"""Interface to the Groq LLM for building ApiCollection objects."""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List

from groq import Groq

from .models import ApiCollection, NoirEndpoint
from .schema import API_COLLECTION_SCHEMA

LOGGER = logging.getLogger(__name__)


class GroqError(RuntimeError):
    """Raised when the Groq API fails."""


def build_api_collection(base_url: str, noir_endpoints: List[NoirEndpoint], route_files: List[Dict[str, str]]) -> ApiCollection:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise GroqError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)

    payload = {
        "baseUrl": base_url,
        "noirEndpoints": [endpoint.dict(by_alias=True) for endpoint in noir_endpoints],
        "routeFiles": route_files,
    }

    system_msg = {
        "role": "system",
        "content": (
            "You are an API architect. Merge Noir endpoints with the provided route files, "
            "infer missing endpoints, and respond ONLY with valid JSON following the schema."
        ),
    }
    user_msg = {"role": "user", "content": json.dumps(payload)}

    LOGGER.info("Requesting Groq API to synthesize ApiCollection")
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

    return collection
