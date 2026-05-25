"""Optional smoke tests against the real API (skipped in CI and without a key)."""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY", "").strip()
    or os.environ.get("OPENROUTER_API_KEY", "").startswith("sk-test"),
    reason="Set a real OPENROUTER_API_KEY to run integration tests",
)
def test_smoke_calificar_respuesta_real_api():
    from grader_agent.grading.text import calificar_respuesta

    rubrica = "## Pregunta 1 (10 puntos)\n**Respuesta esperada:** Menciona el concepto clave.\n"
    out = calificar_respuesta(rubrica, "Pregunta 1", "Concepto clave explicado brevemente.")
    assert "puntaje_obtenido" in out
    assert "puntaje_maximo" in out
