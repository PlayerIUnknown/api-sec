"""Interface for running OWASP Noir scans."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import Iterable, List

from .models import NoirEndpoint

LOGGER = logging.getLogger(__name__)


class NoirError(RuntimeError):
    """Raised when Noir cannot be executed."""


def run_noir(repo_path: str, base_url: str) -> List[NoirEndpoint]:
    """Execute OWASP Noir and parse the resulting endpoints."""

    if not shutil.which("noir"):
        raise NoirError("Noir binary not found in PATH. Please install OWASP Noir.")

    cmd = ["noir", "-b", repo_path, "-u", base_url, "-f", "json", "-T"]
    LOGGER.info("Running Noir: %s", " ".join(cmd))
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", "ignore")
        LOGGER.error("Noir failed: %s", stderr)
        raise NoirError(f"Noir failed: {stderr}") from exc

    stdout = result.stdout.decode("utf-8", "ignore")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError as exc:
        LOGGER.error("Failed to parse Noir output: %s", exc)
        raise NoirError("Noir did not return valid JSON") from exc

    raw_endpoints = _extract_endpoints(payload)

    endpoints = []
    for endpoint in raw_endpoints:
        try:
            endpoints.append(NoirEndpoint(**endpoint))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Skipping malformed Noir endpoint %s: %s", endpoint, exc)
    LOGGER.info("Parsed %d endpoints from Noir", len(endpoints))
    return endpoints


def _extract_endpoints(payload: object) -> Iterable[dict]:
    """Normalize different Noir JSON shapes into a list of endpoints.

    Noir has historically emitted endpoints under a variety of keys and nesting levels
    (e.g. ``endpoints``, ``active_results`` or nested under ``data``/``results``). We
    therefore perform a recursive walk of the JSON payload and collect every mapping
    that looks like an endpoint (it has both ``method`` and ``url`` keys). This is
    defensive but avoids silently returning zero endpoints when Noir succeeds but
    changes its output shape.
    """

    endpoints: List[dict] = []

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            if "method" in obj and "url" in obj:
                endpoints.append(obj)
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(payload)

    if not endpoints:
        top_level_keys: List[str] = []
        if isinstance(payload, dict):
            top_level_keys = list(payload)
        LOGGER.warning(
            "Noir JSON contained no endpoints; top-level keys: %s", top_level_keys
        )

    return endpoints
