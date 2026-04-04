# Evita fallos al importar módulos que instancian OpenAI antes de los mocks.
import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-fake-for-pytest")

import pytest

import grader_agent.web.app as app_module


@pytest.fixture
def app_client(monkeypatch, tmp_path):
    rubrics = tmp_path / "rubrics"
    results = tmp_path / "results"
    rubrics.mkdir()
    results.mkdir()
    monkeypatch.setattr(app_module, "RUBRICS_DIR", str(rubrics))
    monkeypatch.setattr(app_module, "RESULTS_DIR", str(results))
    app_module.app.config["TESTING"] = True
    client = app_module.app.test_client()
    return {
        "client": client,
        "rubrics": rubrics,
        "results": results,
    }


def write_rubrica_parcial(rubrics_dir, contenido: str = "## Rubrica\n") -> None:
    (rubrics_dir / "rubrica_activa.md").write_text(contenido, encoding="utf-8")
