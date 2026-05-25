"""Extracción de texto desde entregables .py y .ipynb (nbformat ≥ 4)."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Union

from grader_agent.grading_config import code_max_bytes, code_max_chars
from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult

_logger = logging.getLogger(__name__)


def _source_from_cell(cell: dict) -> str:
    raw = cell.get("source", "")
    if isinstance(raw, list):
        return "".join(str(x) for x in raw)
    return str(raw)


class CodeNotebookExtractionService:
    """Lee .py (UTF-8) o .ipynb (celdas code) y devuelve texto plano para el pipeline."""

    def extract(self, file_path: str, *, request_id: str | None = None) -> Union[str, ErrorResult]:
        if request_id:
            _logger.debug("code_notebook_extract request_id=%s path=%s", request_id, file_path)
        path = (file_path or "").strip()
        if not path:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="La ruta del archivo de código está vacía.",
                detail=None,
            )
        p = Path(path)
        if not p.is_file():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo de entrega no existe o no es un archivo regular.",
                detail=path,
            )
        try:
            st = p.stat()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo acceder al archivo de entrega.",
                detail=str(exc),
            )
        max_b = code_max_bytes()
        if st.st_size > max_b:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message=(
                    f"El archivo supera el tamaño máximo permitido para código/notebook "
                    f"({max_b} bytes). Acotá el entregable o subí GRADER_CODE_MAX_BYTES."
                ),
                detail=None,
            )

        suffix = p.suffix.lower()
        if suffix == ".py":
            return self._extract_python(p)
        if suffix == ".ipynb":
            return self._extract_notebook(p)
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Solo se aceptan archivos .py o .ipynb para este tipo de entrega.",
            detail=suffix,
        )

    def _apply_char_limit(self, text: str) -> str | ErrorResult:
        max_c = code_max_chars()
        if len(text) <= max_c:
            return text
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message=(
                f"El texto extraído supera el máximo de {max_c} caracteres. "
                "Acotá el archivo o subí GRADER_CODE_MAX_CHARS."
            ),
            detail=None,
        )

    def _extract_python(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo Python.",
                detail=str(exc),
            )
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .py no es UTF-8 válido.",
                detail=None,
            )
        text = text.strip()
        if not text:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .py está vacío o solo tiene espacios.",
                detail=None,
            )
        return self._apply_char_limit(text)

    def _extract_notebook(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el notebook.",
                detail=str(exc),
            )
        try:
            data = json.loads(raw_bytes.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El .ipynb no es JSON UTF-8 válido.",
                detail=str(exc),
            )
        if not isinstance(data, dict):
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El notebook JSON debe ser un objeto en la raíz.",
                detail=None,
            )
        try:
            nb = int(data.get("nbformat", 0))
        except (TypeError, ValueError):
            nb = 0
        if nb < 4:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="Solo se admiten notebooks con nbformat mayor o igual a 4.",
                detail=f"nbformat={data.get('nbformat')!r}",
            )
        cells = data.get("cells")
        if not isinstance(cells, list):
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El notebook no tiene una lista «cells» válida.",
                detail=None,
            )
        parts: list[str] = []
        for i, cell in enumerate(cells):
            if not isinstance(cell, dict):
                continue
            if cell.get("cell_type") != "code":
                continue
            src = _source_from_cell(cell).strip()
            if not src:
                continue
            parts.append(f"# --- celda código {i} ---\n{src}")
        texto = "\n\n".join(parts).strip()
        if not texto:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El notebook no contiene celdas de código con texto.",
                detail=None,
            )
        return self._apply_char_limit(texto)


__all__ = ["CodeNotebookExtractionService"]
