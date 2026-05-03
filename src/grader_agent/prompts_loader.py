"""Carga y compone system prompts desde Markdown del paquete (o GRADER_AGENT_PROMPTS_DIR).

Los contenidos se cachean en memoria (lru_cache) durante la vida del proceso: si se
editan los .md en disco, hay que reiniciar el proceso (o usar otra ruta resuelta en
GRADER_AGENT_PROMPTS_DIR) para que se recarguen.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from grader_agent.prompt_front_matter import strip_yaml_front_matter

_PKG_DIR = Path(__file__).resolve().parent
_DEFAULT_PROMPTS_DIR = _PKG_DIR / "prompts"


def _prompts_dir() -> Path:
    """Carpeta de prompts. Si GRADER_AGENT_PROMPTS_DIR es relativa, resolve() usa el cwd del proceso."""
    raw = os.environ.get("GRADER_AGENT_PROMPTS_DIR", "").strip()
    return Path(raw).resolve() if raw else _DEFAULT_PROMPTS_DIR


def _prompts_root() -> str:
    return str(_prompts_dir().resolve())


@lru_cache(maxsize=64)
def _read_cached(root: str, name: str) -> str:
    path = Path(root) / name
    raw = path.read_text(encoding="utf-8")
    return strip_yaml_front_matter(raw).strip()


def _read_relative(name: str) -> str:
    """Lee un archivo bajo el directorio de prompts; `name` debe ser un literal fijo del paquete."""
    return _read_cached(_prompts_root(), name)


@lru_cache(maxsize=32)
def _merge_evaluator_puntaje_cached(root: str, body_file: str) -> str:
    base = _read_cached(root, "_base_evaluador_puntaje.md")
    body = _read_cached(root, body_file)
    return "\n\n".join((base, body))


def _merge_evaluator_puntaje_only(body_file: str) -> str:
    return _merge_evaluator_puntaje_cached(_prompts_root(), body_file)


@lru_cache(maxsize=32)
def _merge_retro_cached(root: str, body_file: str) -> str:
    body = _read_cached(root, body_file)
    retro = _read_cached(root, "_retro_alumno.md")
    return "\n\n".join((body, retro))


def _merge_retro_only(body_file: str) -> str:
    return _merge_retro_cached(_prompts_root(), body_file)


def system_prompt_pdf_listar_criterios() -> str:
    return _read_relative("pdf_listar_criterios.md")


def system_prompt_pdf_puntaje_criterio() -> str:
    return _merge_evaluator_puntaje_only("pdf_puntaje_criterio.md")


def system_prompt_pdf_retro_criterio() -> str:
    return _merge_retro_only("pdf_retro_criterio.md")


def system_prompt_texto_escala_item() -> str:
    return _read_relative("texto_escala_item.md")


def system_prompt_texto_puntaje_item() -> str:
    return _merge_evaluator_puntaje_only("texto_puntaje_item.md")


def system_prompt_texto_retro_item() -> str:
    return _merge_retro_only("texto_retro_item.md")


def system_prompt_validacion_capa_b() -> str:
    """System prompt para la capa B de validación de contenido (JSON de veredicto)."""
    return _read_relative("validacion_capa_b.md")


def system_prompt_investigador_rubrica() -> str:
    """System prompt for the rubric researcher agent (citation-bound JSON output)."""
    return _read_relative("investigador_rubrica.md")
