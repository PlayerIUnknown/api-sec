"""High-level orchestration of the Noir API Mapper workflow."""

from __future__ import annotations

import logging
from contextlib import contextmanager

from .code_analyzer import extract_route_files
from .groq_processor import GroqError, build_api_collection
from .models import ApiCollection
from .noir_runner import NoirError, run_noir
from .postman import build_postman_collection, save_postman_collection
from .repo_manager import RepoError, cleanup_repo, clone_or_use_repo

LOGGER = logging.getLogger(__name__)


@contextmanager
def _repo_context(repo: str):
    repo_path, cleanup_dir = clone_or_use_repo(repo)
    try:
        yield repo_path
    finally:
        cleanup_repo(cleanup_dir)


def generate_api_collection(repo: str, base_url: str) -> ApiCollection:
    with _repo_context(repo) as repo_path:
        noir_endpoints = run_noir(repo_path, base_url)
        route_files = extract_route_files(repo_path)
        collection = build_api_collection(base_url, noir_endpoints, route_files)
    return collection


def run_pipeline(repo: str, base_url: str, output_path: str) -> str:
    LOGGER.info("Starting pipeline for repo=%s base_url=%s", repo, base_url)
    collection = generate_api_collection(repo, base_url)
    postman = build_postman_collection(collection)
    save_postman_collection(postman, output_path)
    LOGGER.info("Pipeline finished successfully")
    return output_path
