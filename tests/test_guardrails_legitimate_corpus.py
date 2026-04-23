"""Fase 7.3 — textos académicos legítimos no deben ser rechazados por la capa regex."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from grader_agent.guardrails.regex_layer import scan_text_for_policy_violations
from grader_agent.services.content_validation import ContentValidationService

_CORPUS_DIR = Path(__file__).resolve().parent / "fixtures" / "legitimate_corpus"


def _legitimate_samples() -> list[Path]:
    paths = sorted(_CORPUS_DIR.glob("*.txt"))
    assert len(paths) >= 10, "Se esperaban al menos 10 muestras en legitimate_corpus/"
    return paths


@pytest.mark.parametrize("sample_path", _legitimate_samples(), ids=lambda p: p.name)
def test_legitimate_sample_has_no_regex_hits(sample_path: Path) -> None:
    text = sample_path.read_text(encoding="utf-8")
    assert scan_text_for_policy_violations(text) == []


def test_legitimate_corpus_passes_content_validation_regex_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SKIP_LLM_VALIDATION", "true")
    openrouter = MagicMock()
    svc = ContentValidationService(openrouter)
    for sample_path in _legitimate_samples():
        text = sample_path.read_text(encoding="utf-8")
        res = svc.validate(text, request_id="pytest-legit")
        assert res.verdict == "clean", f"{sample_path.name}: {res.reason}"
        assert res.detection_layer == "regex_only"
    openrouter.chat.completions.create.assert_not_called()
