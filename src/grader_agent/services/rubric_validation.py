"""3.4 — Lightweight structural checks on active rubric markdown."""

from __future__ import annotations

import re
from typing import Union

from grader_agent.models import ERROR_TYPE_RUBRIC, ErrorResult

_PERCENT_PATTERN = re.compile(r"\d\s*%|\d+%")


class RubricValidationService:
    """Ensures rubric text is non-empty and minimally structured."""

    def validate(
        self, rubric_markdown: str, *, request_id: str | None = None
    ) -> Union[None, ErrorResult]:
        """
        Paso 3 del pipeline: comprueba que la rúbrica no esté vacía, tenga al menos
        un encabezado Markdown y al menos un porcentaje numérico (``%``).

        Returns:
            ``None`` si la rúbrica pasa los chequeos; ``ErrorResult`` en caso contrario.
        """
        _ = request_id  # reserved for orchestrator / structured logging
        text = (rubric_markdown or "").strip()
        if not text:
            return ErrorResult(
                error_type=ERROR_TYPE_RUBRIC,
                message="La rúbrica está vacía.",
                detail=None,
            )
        if not any(line.lstrip().startswith("#") for line in text.splitlines()):
            return ErrorResult(
                error_type=ERROR_TYPE_RUBRIC,
                message="La rúbrica debe incluir al menos un encabezado Markdown (línea que empiece con #).",
                detail=None,
            )
        if _PERCENT_PATTERN.search(text) is None:
            return ErrorResult(
                error_type=ERROR_TYPE_RUBRIC,
                message="La rúbrica debe incluir al menos un porcentaje numérico (ej. 25% o 20 %).",
                detail=None,
            )
        return None


__all__ = ["RubricValidationService"]
