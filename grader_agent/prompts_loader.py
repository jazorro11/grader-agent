"""Carga y compone system prompts desde Markdown del paquete (o GRADER_AGENT_PROMPTS_DIR)."""

from __future__ import annotations

import os
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
_DEFAULT_PROMPTS_DIR = _PKG_DIR / "prompts"


def _prompts_dir() -> Path:
    """Carpeta de prompts. Si GRADER_AGENT_PROMPTS_DIR es relativa, resolve() usa el cwd del proceso."""
    raw = os.environ.get("GRADER_AGENT_PROMPTS_DIR", "").strip()
    return Path(raw).resolve() if raw else _DEFAULT_PROMPTS_DIR


def _read_relative(name: str) -> str:
    """Lee un archivo bajo el directorio de prompts; `name` debe ser un literal fijo del paquete."""
    path = _prompts_dir() / name
    return path.read_text(encoding="utf-8").strip()


def _merge_evaluator_with_retro(body_file: str) -> str:
    base = _read_relative("_base_evaluador.md")
    retro = _read_relative("_retro_alumno.md")
    body = _read_relative(body_file)
    # Retro al final: las restricciones de tono quedan más cerca de la generación del JSON.
    return "\n\n".join((base, body, retro))


def system_prompt_texto_item() -> str:
    return _merge_evaluator_with_retro("texto_item.md")


def system_prompt_pdf_evaluar_criterio() -> str:
    return _merge_evaluator_with_retro("pdf_evaluar_criterio.md")


def system_prompt_pdf_listar_criterios() -> str:
    return _read_relative("pdf_listar_criterios.md")
