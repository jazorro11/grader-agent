"""3.2 — PDF text extraction with policy limits (PyMuPDF)."""

from __future__ import annotations

import logging
from typing import Union

import fitz  # pymupdf

from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult

_logger = logging.getLogger(__name__)

_MAX_PAGES = 4


class PDFExtractionService:
    """Extract plain text from a PDF with integrity and page-count checks (stateless)."""

    def extract(self, pdf_path: str, *, request_id: str | None = None) -> Union[str, ErrorResult]:
        """
        Paso 1 (PDF): abre el archivo, limita páginas, concatena ``get_text()`` por página.

        Returns:
            Texto plano no vacío o ``ErrorResult`` (archivo inválido, demasiadas páginas, sin texto).
        """
        if request_id:
            _logger.debug("pdf_extract request_id=%s path=%s", request_id, pdf_path)
        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            _logger.info("PDF open failed: %s", exc)
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message=(
                    "El archivo no se pudo leer como PDF (inválido, corrupto o no es PDF). "
                    "Volvé a exportar el entregable e intentá de nuevo."
                ),
                detail=str(exc),
            )

        try:
            n = len(doc)
            if n > _MAX_PAGES:
                return ErrorResult(
                    error_type=ERROR_TYPE_VALIDATION,
                    message=f"El PDF tiene {n} páginas. El máximo permitido es {_MAX_PAGES}.",
                    detail=None,
                )
            parts: list[str] = []
            for pagina in doc:
                parts.append(pagina.get_text())
            texto = "\n".join(parts).strip()
            if not texto:
                return ErrorResult(
                    error_type=ERROR_TYPE_VALIDATION,
                    message="El PDF no contiene texto extraíble (vacío o solo imágenes).",
                    detail=None,
                )
            return texto
        finally:
            doc.close()


__all__ = ["PDFExtractionService"]
