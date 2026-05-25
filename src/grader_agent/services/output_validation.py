"""3.7 — Validate and normalize grading JSON against rubric-derived bounds."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Union

from grader_agent.grading.pdf import metadatos_criterios_desde_rubrica
from grader_agent.grading.score_utils import clamp_puntaje
from grader_agent.models import ERROR_TYPE_INTERNAL, ErrorResult

_logger = logging.getLogger(__name__)

_REQUIRED_ROW_KEYS = frozenset(
    {
        "criterion_name",
        "criterion_weight",
        "level_obtained",
        "level_percentage",
        "weighted_score",
    }
)


def _norm_name(s: object) -> str:
    return " ".join(str(s or "").strip().casefold().split())


class OutputValidationService:
    """
    Ensures grading JSON shape, clamps out-of-range scores, and checks criterion names.

    Stateless service (no LLM): step 5 of the grading pipeline.

    For calificación de un solo ítem de texto, pasá ``allowed_criterion_names`` con el nombre
    canónico del ítem para no exigir todos los criterios del PDF en la rúbrica.
    """

    def validate(
        self,
        grading_json: dict | None,
        rubric_markdown: str,
        *,
        allowed_criterion_names: Sequence[str] | None = None,
        request_id: str | None = None,
    ) -> Union[tuple[dict, list[str]], ErrorResult]:
        """
        Paso 5: normaliza filas, aplica clamps y comprueba nombres de criterio vs la rúbrica.

        Returns:
            ``(payload_normalizado, advertencias)`` o ``ErrorResult`` si la forma es inválida.
        """
        if request_id:
            _logger.debug("output_validation request_id=%s", request_id)
        warnings: list[str] = []

        if not isinstance(grading_json, dict):
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="El JSON de calificación es inválido o no es un objeto.",
                detail="Reintentar la calificación.",
            )

        rows = grading_json.get("scores_by_criterion")
        if not isinstance(rows, list) or not rows:
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="Falta ``scores_by_criterion`` o no es una lista no vacía.",
                detail="Reintentar la calificación.",
            )

        meta = metadatos_criterios_desde_rubrica(rubric_markdown)
        max_by_norm: dict[str, float] = {}
        for m in meta:
            key = _norm_name(m["criterio"])
            try:
                max_by_norm[key] = float(m["puntaje_maximo"])
            except (KeyError, TypeError, ValueError):
                continue

        if allowed_criterion_names is not None:
            expected_set = {_norm_name(x) for x in allowed_criterion_names if str(x).strip()}
        else:
            expected_set = {_norm_name(m["criterio"]) for m in meta}

        if not expected_set:
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="No hay criterios esperados para validar la salida (rúbrica sin metadatos).",
                detail=None,
            )

        def _max_score_for_name(name: object) -> float | None:
            nk = _norm_name(name)
            if nk in max_by_norm:
                return max_by_norm[nk]
            for k, mx in max_by_norm.items():
                if nk in k or k in nk:
                    return mx
            return None

        cleaned_rows: list[dict] = []
        for i, row in enumerate(rows):
            if not isinstance(row, dict):
                return ErrorResult(
                    error_type=ERROR_TYPE_INTERNAL,
                    message=f"La fila {i} de ``scores_by_criterion`` no es un objeto.",
                    detail="Reintentar la calificación.",
                )
            missing = _REQUIRED_ROW_KEYS - row.keys()
            if missing:
                return ErrorResult(
                    error_type=ERROR_TYPE_INTERNAL,
                    message=f"Faltan campos obligatorios en la fila {i}: {', '.join(sorted(missing))}.",
                    detail="Reintentar la calificación.",
                )

            name = row.get("criterion_name")
            nn = _norm_name(name)
            if nn not in expected_set:
                return ErrorResult(
                    error_type=ERROR_TYPE_INTERNAL,
                    message=f"El criterio «{name}» no está entre los criterios esperados.",
                    detail="Reintentar la calificación.",
                )

            try:
                level_pct = float(row.get("level_percentage"))
            except (TypeError, ValueError):
                return ErrorResult(
                    error_type=ERROR_TYPE_INTERNAL,
                    message=f"``level_percentage`` inválido en la fila {i}.",
                    detail="Reintentar la calificación.",
                )

            if level_pct < 0.0 or level_pct > 100.0:
                clamped_lp = max(0.0, min(100.0, level_pct))
                warnings.append(
                    f"WARNING: ``level_percentage`` fuera de rango en fila {i} "
                    f"({level_pct} → {clamped_lp})."
                )
                level_pct = clamped_lp

            mx = _max_score_for_name(name)
            try:
                wscore = float(row.get("weighted_score"))
            except (TypeError, ValueError):
                wscore = 0.0

            if mx is not None:
                clamped_w = clamp_puntaje(wscore, mx)
                if clamped_w != wscore:
                    warnings.append(
                        f"WARNING: ``weighted_score`` fuera de rango en fila {i} "
                        f"({wscore} → {clamped_w}, máx {mx})."
                    )
                    wscore = clamped_w
            else:
                warnings.append(
                    f"WARNING: sin puntaje máximo en rúbrica para «{name}»; "
                    "no se aplicó clamp a ``weighted_score``."
                )

            try:
                cw = float(row.get("criterion_weight"))
            except (TypeError, ValueError):
                cw = 0.0
            if cw < 0.0 or cw > 100.0:
                cwc = max(0.0, min(100.0, cw))
                warnings.append(
                    f"WARNING: ``criterion_weight`` fuera de 0–100 en fila {i} ({cw} → {cwc})."
                )
                cw = cwc

            cleaned_rows.append(
                {
                    "criterion_name": str(name).strip(),
                    "criterion_weight": cw,
                    "level_obtained": str(row.get("level_obtained", "")).strip(),
                    "level_percentage": level_pct,
                    "weighted_score": wscore,
                }
            )

        got_set = {_norm_name(r["criterion_name"]) for r in cleaned_rows}
        if got_set != expected_set:
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="Los criterios en la salida no coinciden exactamente con los esperados.",
                detail="Reintentar la calificación.",
            )

        total_weighted = sum(float(r["weighted_score"]) for r in cleaned_rows)
        total_max = 0.0
        for m in meta:
            if _norm_name(m["criterio"]) in expected_set:
                try:
                    total_max += float(m["puntaje_maximo"])
                except (TypeError, ValueError, KeyError):
                    continue

        if total_max <= 0.0:
            total_max = float(grading_json.get("total_max_score") or 0)

        out = {
            "scores_by_criterion": cleaned_rows,
            "total_weighted_score": total_weighted,
            "total_max_score": total_max,
        }
        for w in warnings:
            _logger.warning("%s", w)
        return out, warnings


__all__ = ["OutputValidationService"]
