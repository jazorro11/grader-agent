# Avoid import failures when modules construct OpenAI clients before mocks.
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-for-pytest")

import pytest

from app import create_app


@pytest.fixture
def app_client(monkeypatch, tmp_path):
    """Isolated data dir: rubrics under ``tmp_path/rubrics``, results at ``tmp_path/resultados.json``."""
    monkeypatch.setenv("GRADER_DATA_DIR", str(tmp_path))
    flask_app = create_app(testing=True)
    client = flask_app.test_client()
    rubrics = tmp_path / "rubrics"
    results = tmp_path
    rubrics.mkdir(parents=True, exist_ok=True)
    return {
        "client": client,
        "app": flask_app,
        "rubrics": rubrics,
        "results": results,
    }


def write_rubrica_parcial(rubrics_dir, contenido: str = "## Rubrica\n") -> None:
    rubrics_dir.mkdir(parents=True, exist_ok=True)
    (rubrics_dir / "rubrica_activa.md").write_text(contenido, encoding="utf-8")
