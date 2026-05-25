"""Fase 7.4 — calibración con LLM real (integración)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from grader_agent.models import DeliveryType, ErrorResult, GradingRequest, GradingResult

pytestmark = pytest.mark.integration

_FIXTURES = Path(__file__).resolve().parent / "fixtures"


def _real_openrouter_key() -> bool:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    return bool(key) and not key.startswith("sk-test")


@pytest.mark.skipif(
    not _real_openrouter_key(),
    reason="Requiere OPENROUTER_API_KEY real (no la clave de prueba de pytest).",
)
def test_reference_rubric_submissions_within_expected_bands(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKIP_LLM_VALIDATION", "true")

    from app.grading_pipeline_factory import create_grading_pipeline

    rubric = (_FIXTURES / "rubrica_referencia.md").read_text(encoding="utf-8")
    manifest = json.loads(
        (_FIXTURES / "entregas_referencia" / "manifest.json").read_text(encoding="utf-8")
    )
    pregunta = str(manifest["pregunta"])
    entregas_dir = _FIXTURES / "entregas_referencia"

    pipeline = create_grading_pipeline()
    passed = 0
    failures: list[str] = []

    for case in manifest["entregas"]:
        answer = (entregas_dir / str(case["archivo"])).read_text(encoding="utf-8")
        content = json.dumps({"pregunta": pregunta, "respuesta": answer}, ensure_ascii=False)
        req = GradingRequest(
            delivery_type=DeliveryType.TEXT,
            content=content,
            student_name="Estudiante de calibración",
            rubric_content=rubric,
        )
        out = pipeline.run(req)
        if isinstance(out, ErrorResult):
            failures.append(f"{case['id']}: {out.error_type} {out.message}")
            continue
        assert isinstance(out, GradingResult)
        lo = float(case["expected_min"])
        hi = float(case["expected_max"])
        score = float(out.total_score)
        if lo <= score <= hi:
            passed += 1
        else:
            failures.append(
                f"{case['id']}: score={score} fuera de [{lo}, {hi}] ({case.get('notas', '')})"
            )

    total = len(manifest["entregas"])
    assert total == 5
    min_ok = int((total * 4 + 4) // 5)
    assert passed >= min_ok, (
        f"Se esperaba ≥80% aciertos ({min_ok}/{total}); "
        f"obtenido {passed}/{total}. Detalles: {failures}"
    )
