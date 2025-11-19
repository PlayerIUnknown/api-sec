"""Convert ApiCollection objects into Postman collections."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List

from .models import ApiCollection, ApiEndpoint, ApiParam

LOGGER = logging.getLogger(__name__)


def _param_to_postman_header(param: ApiParam) -> Dict[str, str]:
    return {
        "key": param.name,
        "value": "",
        "type": "text",
        "description": param.description,
    }


def _build_url(base_var: str, path: str) -> Dict[str, object]:
    normalized = path.lstrip("/")
    segments = [segment for segment in normalized.split("/") if segment]
    return {
        "raw": f"{{{{{base_var}}}}}/" + normalized if normalized else f"{{{{{base_var}}}}}",
        "host": [f"{{{{{base_var}}}}}"],
        "path": segments,
    }


def _endpoint_to_postman(base_var: str, endpoint: ApiEndpoint) -> Dict[str, object]:
    headers = [_param_to_postman_header(header) for header in endpoint.headers]
    query = [
        {
            "key": param.name,
            "value": "",
            "description": param.description,
            "disabled": not param.required,
        }
        for param in endpoint.queryParams
    ]
    body = None
    if endpoint.requestBody:
        example = endpoint.requestBody.get("example") or endpoint.requestBody
        body = {
            "mode": "raw",
            "raw": json.dumps(example, indent=2),
            "options": {"raw": {"language": "json"}},
        }

    url = _build_url(base_var, endpoint.path)
    if query:
        url["query"] = query

    return {
        "name": endpoint.summary or endpoint.path,
        "request": {
            "method": endpoint.method.upper(),
            "header": headers,
            "url": url,
            "description": endpoint.description,
            "body": body,
        },
        "response": [],
    }


def build_postman_collection(collection: ApiCollection) -> Dict[str, object]:
    base_var = "baseUrl"
    items = [_endpoint_to_postman(base_var, endpoint) for endpoint in collection.endpoints]
    postman = {
        "info": {
            "name": collection.title,
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": collection.version,
        },
        "item": items,
        "variable": [{"key": base_var, "value": collection.baseUrl}],
    }
    LOGGER.info("Built Postman collection with %d items", len(items))
    return postman


def save_postman_collection(collection: Dict[str, object], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(collection, handle, indent=2)
    LOGGER.info("Postman collection saved to %s", path)
