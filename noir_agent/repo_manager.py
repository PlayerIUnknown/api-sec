"""Utilities to prepare repositories for analysis."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

LOGGER = logging.getLogger(__name__)


class RepoError(RuntimeError):
    """Raised when a repository cannot be prepared."""


def _is_git_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "ssh"}:
        return True
    return value.endswith(".git")


def clone_or_use_repo(repo: str) -> Tuple[str, str]:
    """Return a tuple of (repo_path, cleanup_dir)."""

    repo_path = Path(repo)
    if repo_path.exists() and repo_path.is_dir():
        LOGGER.info("Using local repository at %s", repo_path)
        return str(repo_path.resolve()), ""

    if not _is_git_url(repo):
        raise RepoError(f"Repository path '{repo}' does not exist and is not a git URL")

    tmp_dir = tempfile.mkdtemp(prefix="noir-repo-")
    LOGGER.info("Cloning %s into %s", repo, tmp_dir)
    try:
        subprocess.run(["git", "clone", "--depth", "1", repo, tmp_dir], check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        shutil.rmtree(tmp_dir, ignore_errors=True)
        stderr = exc.stderr.decode("utf-8", "ignore")
        LOGGER.error("Failed to clone repository: %s", stderr)
        raise RepoError(f"Failed to clone repository: {stderr}") from exc

    return tmp_dir, tmp_dir


def cleanup_repo(cleanup_dir: str) -> None:
    if cleanup_dir and os.path.exists(cleanup_dir):
        LOGGER.info("Cleaning up %s", cleanup_dir)
        shutil.rmtree(cleanup_dir, ignore_errors=True)
