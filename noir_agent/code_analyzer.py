"""Static analysis utilities for discovering routing files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List

LOGGER = logging.getLogger(__name__)

ROUTE_HINTS = {"route", "router", "controller", "urls", "views", "api"}
SUPPORTED_EXTENSIONS = {".js", ".ts", ".py", ".go", ".java", ".kt"}
MAX_FILE_SIZE = 512 * 1024  # 512 KB to avoid massive files
MAX_CONTENT_CHARS = 8_000


def extract_route_files(repo_path: str, limit: int = 25) -> List[Dict[str, str]]:
    """Return a list of probable routing files and short snippets."""

    repo = Path(repo_path)
    if not repo.exists():
        raise FileNotFoundError(repo_path)

    matches: List[Dict[str, str]] = []
    for path in repo.rglob("*"):
        if len(matches) >= limit:
            break
        if not path.is_file() or path.suffix not in SUPPORTED_EXTENSIONS:
            continue
        relative = path.relative_to(repo)
        lower = str(relative).lower()
        if not any(hint in lower for hint in ROUTE_HINTS):
            continue
        try:
            if path.stat().st_size > MAX_FILE_SIZE:
                LOGGER.debug("Skipping %s due to size", path)
                continue
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                content = handle.read(MAX_CONTENT_CHARS)
        except OSError as exc:
            LOGGER.warning("Failed to read %s: %s", path, exc)
            continue
        matches.append({"path": str(path), "content": content})

    LOGGER.info("Identified %d candidate routing files", len(matches))
    return matches
