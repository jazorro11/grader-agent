"""Plain-text submission extraction: reads .txt (UTF-8) and .json submissions."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Union

from grader_agent.grading_config import code_max_bytes, code_max_chars
from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult

_logger = logging.getLogger(__name__)


class PlainTextExtractionService:
    """Reads .txt or .json submission files and returns plain text for grading."""

    def extract(self, file_path: str, *, request_id: str | None = None) -> Union[str, ErrorResult]:
        if request_id:
            _logger.debug("plain_text_extract request_id=%s path=%s", request_id, file_path)
        path = (file_path or "").strip()
        if not path:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="La ruta del archivo de texto está vacía.",
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
                    f"El archivo supera el tamaño máximo permitido "
                    f"({max_b} bytes). Reducí el entregable o subí GRADER_CODE_MAX_BYTES."
                ),
                detail=None,
            )
        suffix = p.suffix.lower()
        if suffix == ".txt":
            return self._extract_txt(p)
        if suffix == ".json":
            return self._extract_json(p)
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Solo se aceptan archivos .txt o .json para este tipo de entrega.",
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

    def _extract_txt(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo de texto.",
                detail=str(exc),
            )
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .txt no es UTF-8 válido.",
                detail=None,
            )
        text = text.strip()
        if not text:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .txt está vacío o solo tiene espacios.",
                detail=None,
            )
        return self._apply_char_limit(text)

    def _extract_json(self, path: Path) -> str | ErrorResult:
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo JSON.",
                detail=str(exc),
            )
        try:
            text = raw_bytes.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo .json no es UTF-8 válido.",
                detail=None,
            )
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El archivo no es JSON válido. Verificá que el entregable esté bien formado.",
                detail=str(exc),
            )
        if not data:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El JSON no contiene contenido evaluable.",
                detail=None,
            )
        serialized = json.dumps(data, ensure_ascii=False, indent=2)
        return self._apply_char_limit(serialized)


__all__ = ["PlainTextExtractionService"]
