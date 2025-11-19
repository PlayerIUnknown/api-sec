"""Interface for running OWASP Noir scans."""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from typing import List

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

    endpoints = []
    for endpoint in payload.get("endpoints", []):
        try:
            endpoints.append(NoirEndpoint(**endpoint))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.warning("Skipping malformed Noir endpoint %s: %s", endpoint, exc)
    LOGGER.info("Parsed %d endpoints from Noir", len(endpoints))
    return endpoints
