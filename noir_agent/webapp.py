"""Flask web UI for Noir API Mapper."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Optional

from flask import Flask, flash, redirect, render_template, request, send_from_directory, url_for

from .pipeline import run_pipeline

LOGGER = logging.getLogger(__name__)


def create_app() -> Flask:
    app = Flask(__name__)
    secret_key = os.getenv("FLASK_SECRET_KEY")
    if not secret_key:
        raise RuntimeError("FLASK_SECRET_KEY is not set")
    app.secret_key = secret_key

    output_dir = Path("out")
    output_dir.mkdir(exist_ok=True)

    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

    @app.route("/generate", methods=["POST"])
    def generate():
        repo = request.form.get("repo", "").strip()
        base_url = request.form.get("base_url", "").strip()
        if not repo or not base_url:
            flash("Repository and Base URL are required", "error")
            return redirect(url_for("index"))
        filename = f"postman_{hashlib.sha1((repo + base_url).encode()).hexdigest()[:10]}.json"
        output_path = output_dir / filename
        try:
            run_pipeline(repo, base_url, str(output_path))
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("Pipeline failed")
            flash(str(exc), "error")
            return redirect(url_for("index"))
        with output_path.open("r", encoding="utf-8") as handle:
            preview = json.load(handle)
        return render_template(
            "result.html",
            filename=filename,
            preview=json.dumps(preview, indent=2),
        )

    @app.route("/download/<path:filename>")
    def download(filename: str):
        safe_path = Path(filename).name
        return send_from_directory(output_dir, safe_path, as_attachment=True)

    return app


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(name)s: %(message)s")
    create_app().run(host="0.0.0.0", port=8000)
