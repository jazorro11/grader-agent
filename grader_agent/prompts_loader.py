from __future__ import annotations

import os
from pathlib import Path

_PKG_DIR = Path(__file__).resolve().parent
_DEFAULT_PROMPTS_DIR = _PKG_DIR / "prompts"


def _prompts_dir() -> Path:
    raw = os.environ.get("GRADER_AGENT_PROMPTS_DIR", "").strip()
    return Path(raw).resolve() if raw else _DEFAULT_PROMPTS_DIR


def _read_relative(name: str) -> str:
    """Lee un archivo bajo el directorio de prompts; `name` debe ser un literal fijo del paquete."""
    path = _prompts_dir() / name
    return path.read_text(encoding="utf-8").strip()


def _merge_with_base(body_file: str) -> str:
    base = _read_relative("_base_evaluador.md")
    body = _read_relative(body_file)
    return f"{base}\n\n{body}"


def system_prompt_texto_item() -> str:
    return _merge_with_base("texto_item.md")


def system_prompt_pdf_evaluar_criterio() -> str:
    return _merge_with_base("pdf_evaluar_criterio.md")


def system_prompt_pdf_listar_criterios() -> str:
    return _read_relative("pdf_listar_criterios.md")
