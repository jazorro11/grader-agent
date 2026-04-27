"""HTTP boundary: run pipeline and map results to legacy JSON for the demo UI."""

from __future__ import annotations

import json
from typing import Any

from flask import current_app, jsonify

from grader_agent.models import (
    ERROR_TYPE_OPENAI,
    ERROR_TYPE_RUBRIC,
    ERROR_TYPE_VALIDATION,
    CriterionScore,
    DeliveryType,
    ErrorResult,
    GradingRequest,
    GradingResult,
)


def run_grading_request(request: GradingRequest) -> GradingResult | ErrorResult:
    """Execute the app-scoped :class:`~grader_agent.pipeline.GradingPipeline`."""
    pipeline = current_app.config["GRADING_PIPELINE"]
    return pipeline.run(request)


def error_result_http_response(err: ErrorResult) -> tuple[Any, int]:
    """Map :class:`~grader_agent.models.ErrorResult` to ``(jsonify(...), status)``."""
    if err.error_type in (ERROR_TYPE_VALIDATION, ERROR_TYPE_RUBRIC):
        return jsonify({"error": err.message}), 400
    if err.error_type == ERROR_TYPE_OPENAI:
        return (
            jsonify(
                {
                    "error": (
                        "The AI grading service failed or is temporarily unavailable. "
                        "Check your API key, quota, and network, then try again."
                    )
                }
            ),
            502,
        )
    return jsonify({"error": err.message}), 502


def _norm_name(s: str) -> str:
    """Normalize criterion labels for fuzzy matching (casefold + collapse whitespace)."""
    return " ".join(s.strip().casefold().split())


def grading_rejection_message(result: GradingResult) -> str | None:
    """Human-readable reason when ``status == \"rejected\"``."""
    if result.status != "rejected" or result.rejection is None:
        return None
    return result.rejection.rejection_reason


def grading_result_rejection_http_response(result: GradingResult) -> tuple[Any, int] | None:
    """If the outcome is a structured rejection, return HTTP error; else ``None``."""
    msg = grading_rejection_message(result)
    if msg is None:
        return None
    return jsonify({"error": msg}), 400


def grading_result_to_text_audio_ui_dict(result: GradingResult) -> dict[str, Any]:
    """
    Legacy shape for ``/calificar-texto`` and ``/calificar-audio`` responses and JSON log.

    Matches fields read by ``index.html`` (``pregunta``, ``puntaje_*``, ``retroalimentacion``).
    """
    label = (result.item_label or "").strip()
    if not label and result.scores_by_criterion:
        label = next(iter(result.scores_by_criterion.keys()))
    return {
        "pregunta": label,
        "puntaje_obtenido": result.total_score,
        "puntaje_maximo": result.total_max_score,
        "retroalimentacion": result.feedback or "",
        "alumno": (result.student_name or "").strip() or "Alumno",
        **({"transcripcion": result.transcription} if (result.transcription or "").strip() else {}),
    }


def grading_result_to_pdf_ui_dict(
    result: GradingResult,
    *,
    criterios_order: list[str] | None = None,
) -> dict[str, Any]:
    """
    Legacy shape for PDF entregable + tabla / CSV (``criterios``, ``total_*``, ``tipo``).
    """
    scores: dict[str, CriterionScore] = dict(result.scores_by_criterion)
    by_norm: dict[str, str] = {_norm_name(k): k for k in scores}

    criterios: list[dict[str, Any]] = []
    used_norms: set[str] = set()
    global_retro = (result.feedback or "").strip()

    def _row(orig_key: str) -> dict[str, Any]:
        cs = scores[orig_key]
        per = (cs.feedback or "").strip()
        return {
            "criterio": orig_key,
            "puntaje_obtenido": cs.score,
            "puntaje_maximo": cs.max_score,
            "retroalimentacion": per or global_retro,
        }

    order = criterios_order if criterios_order else list(scores.keys())
    for name in order:
        nk = _norm_name(name)
        orig = by_norm.get(nk)
        if orig is None:
            for cand_nk, orig_k in by_norm.items():
                if nk in cand_nk or cand_nk in nk:
                    orig = orig_k
                    break
        if orig is None:
            continue
        on = _norm_name(orig)
        if on in used_norms:
            continue
        used_norms.add(on)
        criterios.append(_row(orig))

    for orig in scores:
        if _norm_name(orig) in used_norms:
            continue
        used_norms.add(_norm_name(orig))
        criterios.append(_row(orig))

    alumno = (result.student_name or "").strip() or "Alumno"
    kind = (result.deliverable_kind or "").strip()
    tipo = (
        "entregable_codigo"
        if kind == DeliveryType.CODE_DELIVERABLE.value
        else "entregable_pdf"
    )
    return {
        "alumno": alumno,
        "tipo": tipo,
        "criterios": criterios,
        "total_obtenido": result.total_score,
        "total_maximo": result.total_max_score,
    }


def build_text_grading_request(
    *,
    rubric: str,
    student_name: str,
    pregunta: str,
    respuesta: str,
) -> GradingRequest:
    """Build a ``TEXT`` pipeline request embedding pregunta/respuesta JSON in ``content``."""
    content = json.dumps(
        {"pregunta": pregunta, "respuesta": respuesta},
        ensure_ascii=False,
    )
    return GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content=content,
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )


def build_audio_grading_request(
    *,
    rubric: str,
    student_name: str,
    pregunta: str,
    audio_path: str,
) -> GradingRequest:
    """Build an ``AUDIO`` request with filesystem path and item label inside ``content`` JSON."""
    content = json.dumps(
        {"path": audio_path, "pregunta": pregunta},
        ensure_ascii=False,
    )
    return GradingRequest(
        delivery_type=DeliveryType.AUDIO,
        content=content,
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )


def build_pdf_grading_request(
    *,
    rubric: str,
    student_name: str,
    pdf_path: str,
) -> GradingRequest:
    """Build a ``PDF_DELIVERABLE`` request whose ``content`` is the PDF path string."""
    return GradingRequest(
        delivery_type=DeliveryType.PDF_DELIVERABLE,
        content=pdf_path.strip(),
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )


def build_code_deliverable_grading_request(
    *,
    rubric: str,
    student_name: str,
    file_path: str,
) -> GradingRequest:
    """Build a ``CODE_DELIVERABLE`` request (``.py`` / ``.ipynb``) whose ``content`` is the file path."""
    return GradingRequest(
        delivery_type=DeliveryType.CODE_DELIVERABLE,
        content=file_path.strip(),
        student_name=student_name.strip() or "Alumno",
        rubric_content=rubric,
    )
