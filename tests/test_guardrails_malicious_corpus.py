"""Fase 7.2 — corpus malicioso: cada muestra debe disparar la capa regex."""

from __future__ import annotations

from pathlib import Path

import pytest

from grader_agent.guardrails.regex_layer import scan_text_for_policy_violations

_CORPUS_DIR = Path(__file__).resolve().parent / "fixtures" / "malicious_corpus"


def _malicious_samples() -> list[Path]:
    paths = sorted(_CORPUS_DIR.glob("*.txt"))
    assert len(paths) >= 25, "Se esperaban al menos 25 muestras .txt en malicious_corpus/"
    return paths


@pytest.mark.parametrize("sample_path", _malicious_samples(), ids=lambda p: p.name)
def test_malicious_sample_triggers_regex_layer(sample_path: Path) -> None:
    text = sample_path.read_text(encoding="utf-8")
    hits = scan_text_for_policy_violations(text)
    assert hits, f"{sample_path.name} debería producir al menos un hallazgo regex"


def test_malicious_corpus_has_expected_cardinality() -> None:
    assert len(_malicious_samples()) >= 25
