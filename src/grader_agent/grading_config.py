"""Temperaturas y parámetros de calificación desde variables de entorno."""

from __future__ import annotations

import os
from typing import Literal

# Default max output tokens for chat completions (model set via LLM_MODEL / GRADER_CHAT_MODEL).
_DEFAULT_MAX_COMPLETION_ESCALA = 256
_DEFAULT_MAX_COMPLETION_PUNTAJE = 256
_DEFAULT_MAX_COMPLETION_LISTAR = 8192
_DEFAULT_MAX_COMPLETION_RETRO = 4096
_DEFAULT_MAX_COMPLETION_GRADING_JSON = 1024
_DEFAULT_PDF_MAX_PAGES = 4
_DEFAULT_CODE_MAX_BYTES = 524_288
_DEFAULT_CODE_MAX_CHARS = 400_000


def _int_env(name: str, default: int, *, minimum: int = 1) -> int:
    """Entero desde env; vacío o no numérico → default; resultado ≥ minimum."""
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        v = int(raw)
    except ValueError:
        return default
    return max(minimum, v)


def pdf_max_pages() -> int:
    """Máximo de páginas por PDF aceptadas para extracción de texto (PyMuPDF)."""
    return _int_env("GRADER_PDF_MAX_PAGES", _DEFAULT_PDF_MAX_PAGES)


def code_max_bytes() -> int:
    """Tamaño máximo en bytes del archivo .py o .ipynb leído desde disco."""
    return _int_env("GRADER_CODE_MAX_BYTES", _DEFAULT_CODE_MAX_BYTES, minimum=1024)


def code_max_chars() -> int:
    """Longitud máxima del texto extraído (código / notebook) tras decodificar."""
    return _int_env("GRADER_CODE_MAX_CHARS", _DEFAULT_CODE_MAX_CHARS, minimum=4096)


CompletionKind = Literal["escala", "puntaje", "listar", "retro", "validation", "grading_json"]


def max_completion_tokens_escala() -> int:
    """Tope de salida para ubicar ítem/escala en la rúbrica (JSON corto)."""
    return _int_env("GRADER_MAX_COMPLETION_ESCALA", _DEFAULT_MAX_COMPLETION_ESCALA)


def max_completion_tokens_puntaje() -> int:
    """Tope de salida para llamadas que solo devuelven puntaje numérico."""
    return _int_env("GRADER_MAX_COMPLETION_PUNTAJE", _DEFAULT_MAX_COMPLETION_PUNTAJE)


def max_completion_tokens_listar_criterios() -> int:
    """Tope de salida para extraer la lista de criterios desde la rúbrica."""
    return _int_env("GRADER_MAX_COMPLETION_LISTAR", _DEFAULT_MAX_COMPLETION_LISTAR)


def max_completion_tokens_retro() -> int:
    """Tope de salida para retroalimentación al alumno."""
    return _int_env("GRADER_MAX_COMPLETION_RETRO", _DEFAULT_MAX_COMPLETION_RETRO)


def max_completion_tokens_grading_json() -> int:
    """Tope de salida para JSON estructurado de calificación (``scores_by_criterion``)."""
    return _int_env("GRADER_MAX_COMPLETION_GRADING_JSON", _DEFAULT_MAX_COMPLETION_GRADING_JSON)


def max_completion_tokens_validation() -> int:
    """Tope de salida para validación de contenido (JSON corto)."""
    from grader_agent.settings import validation_max_tokens

    return validation_max_tokens()


def chat_completion_limit_kwargs(*, kind: CompletionKind) -> dict[str, int]:
    """Argumentos para client.chat.completions.create (max_completion_tokens)."""
    mapping: dict[str, int] = {
        "escala": max_completion_tokens_escala(),
        "puntaje": max_completion_tokens_puntaje(),
        "listar": max_completion_tokens_listar_criterios(),
        "retro": max_completion_tokens_retro(),
        "validation": max_completion_tokens_validation(),
        "grading_json": max_completion_tokens_grading_json(),
    }
    if kind not in mapping:
        raise ValueError(f"kind inválido: {kind!r}")
    return {"max_completion_tokens": mapping[kind]}


def score_temperature() -> float:
    """Temperatura para la decisión de puntaje (por defecto 0, más estable)."""
    raw = os.environ.get("GRADER_SCORE_TEMPERATURE", "").strip()
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def retro_temperature() -> float:
    """Temperatura para la retroalimentación al alumno (por defecto más creativa)."""
    raw = os.environ.get("GRADER_RETRO_TEMPERATURE", "").strip()
    if not raw:
        return 0.8
    try:
        return float(raw)
    except ValueError:
        return 0.8
