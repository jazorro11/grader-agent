"""Central environment-backed settings (paths, models, validation)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _project_root() -> Path:
    """Repo root (parent of ``src/``)."""
    return Path(__file__).resolve().parents[2]


def _default_data_dir() -> Path:
    return _project_root() / "data"


@dataclass(frozen=True)
class GraderPaths:
    """Writable runtime paths under ``GRADER_DATA_DIR``."""

    data_dir: Path
    rubrics_dir: Path
    active_rubric_file: Path
    results_json: Path

    @classmethod
    def from_env(cls) -> GraderPaths:
        raw = os.environ.get("GRADER_DATA_DIR", "").strip()
        base = Path(raw).resolve() if raw else _default_data_dir().resolve()
        rubrics = base / "rubrics"
        return cls(
            data_dir=base,
            rubrics_dir=rubrics,
            active_rubric_file=rubrics / "rubrica_activa.md",
            results_json=base / "resultados.json",
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rubrics_dir.mkdir(parents=True, exist_ok=True)


def chat_model() -> str:
    return os.environ.get("GRADER_CHAT_MODEL", "gpt-4o").strip() or "gpt-4o"


def transcription_model() -> str:
    return (
        os.environ.get("GRADER_TRANSCRIPTION_MODEL", "whisper-1").strip()
        or "whisper-1"
    )


def transcription_language() -> str:
    return os.environ.get("GRADER_TRANSCRIPTION_LANGUAGE", "es").strip() or "es"


def validate_openai_api_key_for_runtime(*, testing: bool) -> None:
    """
    Ensure ``OPENAI_API_KEY`` is set for real runs.

    Skips when ``testing`` is True (e.g. Flask TESTING or pytest).
    """
    if testing:
        return
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy `.env.example` to `.env` and add your key."
        )
