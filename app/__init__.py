"""Flask application factory for the multimodal grading demo."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask

from app.routes import register_routes
from grader_agent.http_logging import configure_logging, register_http_logging
from grader_agent.settings import GraderPaths, validate_openai_api_key_for_runtime


def create_app(*, testing: bool | None = None) -> Flask:
    """
    Build and configure the Flask app.

    Args:
        testing: If True, skip OpenAI API key validation (pytest). If None, uses
            ``app.testing`` after it is set from ``TESTING`` env when present.
    """
    load_dotenv()
    configure_logging()

    template_dir = Path(__file__).resolve().parent / "templates"
    app = Flask(__name__, template_folder=str(template_dir))

    if testing is not None:
        app.config["TESTING"] = testing
    else:
        app.config["TESTING"] = os.environ.get("FLASK_TESTING", "").lower() in (
            "1",
            "true",
            "yes",
        )

    validate_openai_api_key_for_runtime(testing=bool(app.config["TESTING"]))

    paths = GraderPaths.from_env()
    paths.ensure_directories()
    app.config["GRADER_PATHS"] = paths

    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

    register_http_logging(app)
    register_routes(app)

    return app
