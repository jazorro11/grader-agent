"""Unit tests for the research cache layer (hashing, atomic IO, corruption)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from grader_agent.services.research_cache import (
    delete_cached,
    read_cached,
    rubric_hash,
    write_cached,
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


def test_rubric_hash_is_stable_against_whitespace_changes() -> None:
    a = "# Rúbrica\n\nCriterio 25%\n"
    b = "  # Rúbrica\n\n   Criterio 25%   \n\n\n"
    assert rubric_hash(a) == rubric_hash(b)


def test_rubric_hash_changes_with_content() -> None:
    assert rubric_hash("# Rúbrica A") != rubric_hash("# Rúbrica B")


def test_read_cached_returns_none_when_missing(paths: GraderPaths) -> None:
    assert read_cached(paths, "nope") is None


def test_write_then_read_round_trip(paths: GraderPaths) -> None:
    digest = rubric_hash("# Rubric")
    payload = {
        "temas": [{"tema": "T1", "hechos": ["h1"], "errores_frecuentes": [], "citas": []}],
        "advertencias": [],
    }
    write_cached(paths, digest, guide_markdown="# Guía", payload=payload)
    cached = read_cached(paths, digest)
    assert cached is not None
    assert cached.rubric_hash == digest
    assert cached.guide_markdown == "# Guía"
    assert cached.payload["temas"][0]["tema"] == "T1"
    assert cached.payload["rubric_hash"] == digest


def test_corrupt_json_sidecar_treated_as_miss(paths: GraderPaths) -> None:
    digest = rubric_hash("# x")
    write_cached(paths, digest, guide_markdown="# G", payload={"temas": []})
    json_path = paths.research_dir / f"{digest}.json"
    json_path.write_text("{not json", encoding="utf-8")
    assert read_cached(paths, digest) is None


def test_empty_guide_treated_as_miss(paths: GraderPaths) -> None:
    digest = rubric_hash("# x")
    write_cached(paths, digest, guide_markdown="   \n", payload={"temas": [{"tema": "t"}]})
    assert read_cached(paths, digest) is None


def test_delete_cached_removes_files(paths: GraderPaths) -> None:
    digest = rubric_hash("# y")
    write_cached(paths, digest, guide_markdown="# G", payload={"temas": []})
    assert (paths.research_dir / f"{digest}.md").is_file()
    assert delete_cached(paths, digest) is True
    assert not (paths.research_dir / f"{digest}.md").exists()
    assert not (paths.research_dir / f"{digest}.json").exists()


def test_atomic_write_does_not_leave_tmp_files(paths: GraderPaths) -> None:
    digest = rubric_hash("# z")
    write_cached(paths, digest, guide_markdown="# G", payload={"temas": []})
    tmps = list(paths.research_dir.glob("*.tmp"))
    assert tmps == []


def test_payload_writes_valid_json(paths: GraderPaths) -> None:
    digest = rubric_hash("# w")
    payload = {"temas": [{"tema": "Té con tilde"}], "advertencias": ["¡cuidado!"]}
    write_cached(paths, digest, guide_markdown="# G", payload=payload)
    data = json.loads((paths.research_dir / f"{digest}.json").read_text(encoding="utf-8"))
    assert data["temas"][0]["tema"] == "Té con tilde"
    assert data["advertencias"] == ["¡cuidado!"]
