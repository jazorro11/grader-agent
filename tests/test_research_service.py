"""Tests for ``RubricResearchService`` (mocking the chat completion call)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from grader_agent.models import ErrorResult
from grader_agent.services.research import (
    GUIDE_HEADING,
    RubricResearchService,
    _filter_payload_citations,
    _normalize_payload,
    render_guide_markdown,
)
from grader_agent.settings import GraderPaths


@pytest.fixture
def paths(tmp_path: Path) -> GraderPaths:
    p = GraderPaths(
        data_dir=tmp_path,
        rubrics_dir=tmp_path / "rubrics",
        active_rubric_file=tmp_path / "rubrics" / "rubrica_activa.md",
        results_json=tmp_path / "resultados.json",
        research_dir=tmp_path / "research",
    )
    p.ensure_directories()
    return p


@pytest.fixture(autouse=True)
def _enable_research_for_module(monkeypatch: pytest.MonkeyPatch) -> None:
    """The shared conftest disables the researcher; re-enable it for these tests."""
    monkeypatch.setenv("SKIP_RESEARCH", "0")


def _good_payload() -> dict:
    return {
        "temas": [
            {
                "tema": "Amplificador instrumental",
                "hechos": ["Aísla la entrada y amplifica la diferencia."],
                "errores_frecuentes": ["Confundir CMRR con SNR."],
                "citas": [
                    {
                        "url": "https://www.analog.com/lit/an/an-244.pdf",
                        "titulo": "Analog Devices — Application Note 244",
                        "tipo": "oficial",
                    }
                ],
            }
        ],
        "advertencias": [],
    }


def test_normalize_payload_drops_invalid_topics() -> None:
    raw = {
        "temas": [
            {"tema": "", "hechos": ["x"]},
            {"tema": "OK", "hechos": [], "errores_frecuentes": []},
            {"tema": "Buena", "hechos": ["dato"], "errores_frecuentes": [], "citas": []},
        ],
        "advertencias": [],
    }
    out = _normalize_payload(raw)
    assert out is not None
    nombres = [t["tema"] for t in out["temas"]]
    assert nombres == ["Buena"]


def test_filter_citations_strips_disallowed_domains() -> None:
    payload = {
        "temas": [
            {
                "tema": "T",
                "hechos": ["h"],
                "errores_frecuentes": [],
                "citas": [
                    {"url": "https://example.com/x", "titulo": "X", "tipo": "oficial"},
                    {"url": "https://ti.com/lit/an", "titulo": "TI", "tipo": "oficial"},
                ],
            }
        ],
        "advertencias": [],
    }
    out = _filter_payload_citations(payload, (".edu", "ti.com"))
    assert len(out["temas"][0]["citas"]) == 1
    assert "ti.com" in out["temas"][0]["citas"][0]["url"]


def test_render_guide_includes_heading_and_citations() -> None:
    md = render_guide_markdown(_good_payload())
    assert md.startswith(GUIDE_HEADING)
    assert "Tema: Amplificador instrumental" in md
    assert "Errores frecuentes" in md
    assert "## Citas" in md
    assert "analog.com" in md


def test_get_or_create_caches_first_call(paths: GraderPaths) -> None:
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)
    rubric = "# Rúbrica de IA\n\n40% IA\n"

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value=json.dumps(_good_payload()),
    ) as mock_call:
        first = service.get_or_create(rubric)
        second = service.get_or_create(rubric)

    assert mock_call.call_count == 1
    assert not isinstance(first, ErrorResult)
    assert not isinstance(second, ErrorResult)
    assert first.rubric_hash == second.rubric_hash
    assert "Amplificador" in first.guide_markdown


def test_get_or_create_whitespace_variant_hits_same_cache(paths: GraderPaths) -> None:
    """Misma rúbrica con espacios distintos → mismo hash (normalización) → una llamada LLM."""
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)
    a = "# Rúbrica de IA\n\n40% IA\n"
    b = "  # Rúbrica de IA\n\n   40% IA   \n"

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value=json.dumps(_good_payload()),
    ) as mock_call:
        service.get_or_create(a)
        service.get_or_create(b)

    assert mock_call.call_count == 1


def test_force_refresh_bypasses_cache(paths: GraderPaths) -> None:
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)
    rubric = "# Rúbrica\n\n40% IA\n"

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value=json.dumps(_good_payload()),
    ) as mock_call:
        service.get_or_create(rubric)
        service.get_or_create(rubric, force_refresh=True)

    assert mock_call.call_count == 2


def test_invalid_json_returns_error_result(paths: GraderPaths) -> None:
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value="not json at all",
    ):
        out = service.investigate("# Rúbrica")

    assert isinstance(out, ErrorResult)
    assert "json inválido" in out.message.lower()


def test_no_allowed_citations_returns_error(paths: GraderPaths) -> None:
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)

    payload = _good_payload()
    payload["temas"][0]["citas"] = [
        {"url": "https://blog.example.com/a", "titulo": "Blog", "tipo": "oficial"}
    ]
    payload["temas"][0]["hechos"] = []  # ensure topic is dropped when citations get filtered

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value=json.dumps(payload),
    ), patch(
        "grader_agent.services.research.research_domain_allowlist",
        return_value=(".edu", ".gov"),
    ):
        out = service.investigate("# Rúbrica")

    assert isinstance(out, ErrorResult)


def test_skip_research_short_circuits(paths: GraderPaths, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SKIP_RESEARCH", "1")  # overrides the fixture for this test only
    service = RubricResearchService(MagicMock(), paths=paths)

    out = service.get_or_create("# Rúbrica\n40%\n")
    assert isinstance(out, ErrorResult)
    assert "deshabilitada" in out.message.lower() or "skip" in out.message.lower()


def test_chat_exception_returns_openai_error(paths: GraderPaths) -> None:
    service = RubricResearchService(MagicMock(), paths=paths)

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        side_effect=RuntimeError("boom"),
    ):
        out = service.investigate("# Rúbrica")

    assert isinstance(out, ErrorResult)
    assert out.error_type == "openai"


def test_get_or_create_persists_payload_metadata(paths: GraderPaths) -> None:
    client = MagicMock()
    service = RubricResearchService(client, paths=paths)
    rubric = "# Rúbrica de IA\n\n40% IA\n"

    with patch(
        "grader_agent.services.research.chat_completion_json_content",
        return_value=json.dumps(_good_payload()),
    ):
        cached = service.get_or_create(rubric)

    assert not isinstance(cached, ErrorResult)
    sidecar = json.loads(
        (paths.research_dir / f"{cached.rubric_hash}.json").read_text(encoding="utf-8")
    )
    assert sidecar["rubric_hash"] == cached.rubric_hash
    assert sidecar["temas"][0]["tema"] == "Amplificador instrumental"
