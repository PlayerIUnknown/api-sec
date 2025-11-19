"""Typer CLI interface for Noir API Mapper."""

from __future__ import annotations

import logging
from pathlib import Path

import typer

from .pipeline import run_pipeline

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")

app = typer.Typer(help="Noir API Mapper CLI")


@app.command("generate")
def generate(
    repo: str = typer.Option(..., "--repo", help="Repository path or git URL"),
    base_url: str = typer.Option(..., "--base-url", help="Base URL of the API"),
    out: Path = typer.Option("postman_collection.json", "--out", help="Output Postman file"),
):
    """Generate a Postman collection from the provided repository."""

    try:
        run_pipeline(repo, base_url, str(out))
    except Exception as exc:  # pylint: disable=broad-except
        logging.exception("Pipeline failed")
        raise typer.Exit(code=1) from exc

    typer.echo(f"Postman collection saved to {out}")


if __name__ == "__main__":
    app()
