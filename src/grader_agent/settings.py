"""Central environment-backed settings (paths, models, validation)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path

_OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

_DEFAULT_LLM_MODEL = "gpt-4o"
_DEFAULT_VALIDATION_MODEL = "gpt-4o-mini"
_DEFAULT_GRADING_MAX_TOKENS = 8192
_DEFAULT_FEEDBACK_MAX_TOKENS = 4096
_DEFAULT_VALIDATION_MAX_TOKENS = 2048

_TRUTHY = frozenset({"1", "true", "yes"})


def _project_root() -> Path:
    """Repo root (parent of ``src/``)."""
    return Path(__file__).resolve().parents[2]


def _default_data_dir() -> Path:
    """Default ``data/`` directory at repo root when ``GRADER_DATA_DIR`` is unset."""
    return _project_root() / "data"


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    return max(minimum, v)


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
        """Create ``data_dir`` and ``rubrics_dir`` if they do not exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.rubrics_dir.mkdir(parents=True, exist_ok=True)


def llm_model() -> str:
    """Primary chat model; ``LLM_MODEL`` wins, then legacy ``GRADER_CHAT_MODEL``."""
    v = os.environ.get("LLM_MODEL", "").strip()
    if v:
        return v
    v = os.environ.get("GRADER_CHAT_MODEL", "").strip()
    if v:
        return v
    return _DEFAULT_LLM_MODEL


def chat_model() -> str:
    """Alias for :func:`llm_model` (existing call sites)."""
    return llm_model()


def transcription_model() -> str:
    """Speech-to-text model id for ``audio.transcriptions`` (default ``whisper-1``)."""
    return os.environ.get("GRADER_TRANSCRIPTION_MODEL", "whisper-1").strip() or "whisper-1"


def transcription_language() -> str:
    """ISO-639-1 hint passed to the transcription API (default ``es``)."""
    return os.environ.get("GRADER_TRANSCRIPTION_LANGUAGE", "es").strip() or "es"


def openrouter_api_key() -> str:
    """Secret for OpenRouter chat completions (trimmed; empty if unset)."""
    return os.environ.get("OPENROUTER_API_KEY", "").strip()


def openai_api_key() -> str:
    """API key for direct OpenAI calls (e.g. Whisper)."""
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openrouter_base_url() -> str:
    """Chat API base URL for the OpenRouter-compatible OpenAI SDK client."""
    return _OPENROUTER_BASE_URL


def validation_llm_model() -> str:
    """Chat model id for layer B content validation (default ``gpt-4o-mini``)."""
    return (
        os.environ.get("VALIDATION_LLM_MODEL", _DEFAULT_VALIDATION_MODEL).strip()
        or _DEFAULT_VALIDATION_MODEL
    )


def skip_llm_validation() -> bool:
    """Return True when ``SKIP_LLM_VALIDATION`` is a truthy string (skip layer B)."""
    raw = os.environ.get("SKIP_LLM_VALIDATION", "").strip().lower()
    return raw in _TRUTHY


def grading_max_tokens() -> int:
    """Max completion tokens for grading JSON calls (env ``GRADING_MAX_TOKENS``)."""
    return _int_env("GRADING_MAX_TOKENS", _DEFAULT_GRADING_MAX_TOKENS)


def feedback_max_tokens() -> int:
    """Max completion tokens for student feedback calls (env ``FEEDBACK_MAX_TOKENS``)."""
    return _int_env("FEEDBACK_MAX_TOKENS", _DEFAULT_FEEDBACK_MAX_TOKENS)


def validation_max_tokens() -> int:
    """Max completion tokens for validation calls (env ``VALIDATION_MAX_TOKENS``)."""
    return _int_env("VALIDATION_MAX_TOKENS", _DEFAULT_VALIDATION_MAX_TOKENS)


def log_file_path() -> Path | None:
    """Optional absolute path for file logging; ``None`` if ``LOG_FILE_PATH`` is empty."""
    raw = os.environ.get("LOG_FILE_PATH", "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def log_level() -> int:
    """Numeric logging level from ``LOG_LEVEL`` (defaults to ``logging.INFO``)."""
    raw = os.environ.get("LOG_LEVEL", "INFO").strip().upper() or "INFO"
    level = getattr(logging, raw, None)
    if not isinstance(level, int):
        return logging.INFO
    return level


def validate_llm_api_keys_for_runtime(*, testing: bool) -> None:
    """
    Ensure ``OPENAI_API_KEY`` (Whisper) and ``OPENROUTER_API_KEY`` (chat) are set.

    Skips when ``testing`` is True (e.g. Flask TESTING or pytest).
    """
    if testing:
        return
    if not openai_api_key():
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy `.env.example` to `.env` and add your key."
        )
    if not openrouter_api_key():
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy `.env.example` to `.env` and add your key."
        )
