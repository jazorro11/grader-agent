"""Fase 4 — Orquestador secuencial del flujo de calificación (pasos 0–6)."""

from __future__ import annotations

import json
import logging
import uuid
from typing import Union

from grader_agent.grading.pdf import metadatos_criterios_desde_rubrica
from grader_agent.grading.text import escala_item_desde_rubrica
from grader_agent.models import (
    ERROR_TYPE_INTERNAL,
    ERROR_TYPE_VALIDATION,
    CriterionScore,
    DeliveryType,
    ErrorResult,
    GradingRequest,
    GradingRejection,
    GradingResult,
)
from grader_agent.services.content_validation import ContentValidationService
from grader_agent.services.feedback import FeedbackService
from grader_agent.services.grading import GradingService
from grader_agent.services.output_validation import OutputValidationService
from grader_agent.services.code_notebook_extraction import CodeNotebookExtractionService
from grader_agent.services.pdf_extraction import PDFExtractionService
from grader_agent.services.plain_text_extraction import PlainTextExtractionService
from grader_agent.services.research import RubricResearchService
from grader_agent.services.rubric_validation import RubricValidationService
from grader_agent.services.transcription import TranscriptionService

_logger = logging.getLogger(__name__)


def _coerce_delivery_type(value: object) -> DeliveryType | ErrorResult:
    if isinstance(value, DeliveryType):
        return value
    if isinstance(value, str):
        try:
            return DeliveryType(value)
        except ValueError:
            pass
    return ErrorResult(
        error_type=ERROR_TYPE_VALIDATION,
        message="Tipo de entrega inválido.",
        detail=f"Se esperaba uno de: {[e.value for e in DeliveryType]}.",
    )


def _parse_text_submission(content: str) -> tuple[str, str] | ErrorResult:
    """
    Para ``DeliveryType.TEXT``: JSON con pregunta/ítem y respuesta, o texto plano
    como respuesta única (la pregunta/ítem debe ir en el JSON según contrato HTTP).
    """
    raw = (content or "").strip()
    if not raw:
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="El contenido de la entrega de texto está vacío.",
            detail=None,
        )
    if not raw.startswith("{"):
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Para entrega de texto se requiere JSON con «pregunta» y «respuesta».",
            detail='Ejemplo: {"pregunta": "Ítem 1", "respuesta": "..."}',
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="El contenido de texto no es JSON válido.",
            detail=str(exc),
        )
    if not isinstance(data, dict):
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="El JSON de entrega de texto debe ser un objeto.",
            detail=None,
        )
    q = str(data.get("pregunta") or data.get("item") or "").strip()
    ans = str(
        data.get("respuesta") or data.get("respuesta_alumno") or data.get("answer") or ""
    ).strip()
    if not q:
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Falta la pregunta o ítem (campo «pregunta») en el JSON de entrega.",
            detail=None,
        )
    if not ans:
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Falta la respuesta del estudiante en el JSON de entrega.",
            detail=None,
        )
    return ans, q


def _parse_audio_delivery(
    content: str,
    rubric_markdown: str,
) -> tuple[str, str] | ErrorResult:
    """
    Resuelve ruta de audio y pregunta/ítem.

    Se acepta JSON ``{"path"|"audio_path"|"archivo": "...", "pregunta": "..."}`` o una ruta
    plana si la rúbrica define un único criterio (la etiqueta del criterio se usa como ítem).
    """
    raw = (content or "").strip()
    audio_path = ""
    item_q = ""
    if raw.startswith("{"):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El contenido de audio no es JSON válido.",
                detail=str(exc),
            )
        if not isinstance(data, dict):
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El JSON de audio debe ser un objeto.",
                detail=None,
            )
        audio_path = str(
            data.get("path") or data.get("audio_path") or data.get("archivo") or ""
        ).strip()
        item_q = str(data.get("pregunta") or data.get("item") or "").strip()
        if not audio_path:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="Falta la ruta del archivo de audio en el JSON (clave «path» o similar).",
                detail=None,
            )
    else:
        audio_path = raw

    if not audio_path:
        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="La ruta del audio está vacía.",
            detail=None,
        )

    if not item_q:
        meta = metadatos_criterios_desde_rubrica(rubric_markdown)
        if len(meta) == 1:
            item_q = str(meta[0]["criterio"])
        else:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message=(
                    "Para audio sin «pregunta» en JSON, la rúbrica debe tener exactamente un criterio, "
                    "o incluí «pregunta» junto a la ruta en JSON."
                ),
                detail=None,
            )
    return audio_path, item_q


def _submission_body_heading(delivery: DeliveryType, artifact_path: str) -> str:
    """Encabezado del bloque de entrega en el prompt de calificación multi-criterio."""
    if delivery == DeliveryType.PDF_DELIVERABLE:
        low = (artifact_path or "").lower()
        if low.endswith(".docx"):
            return "TEXTO PLANO DEL ENTREGABLE (DOCX)"
        return "TEXTO PLANO DEL ENTREGABLE (PDF)"
    if delivery == DeliveryType.CODE_DELIVERABLE:
        low = artifact_path.lower()
        if low.endswith(".ipynb"):
            return "CONTENIDO EXTRAÍDO DEL NOTEBOOK (celdas de código, en orden)"
        return "CÓDIGO FUENTE DEL ARCHIVO PYTHON"
    if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
        low = (artifact_path or "").lower()
        if low.endswith(".json"):
            return "CONTENIDO JSON DEL ENTREGABLE"
        return "TEXTO PLANO DEL ENTREGABLE (TXT)"
    return "TEXTO PLANO DEL ENTREGABLE (PDF)"


def _grading_internal_recoverable(err: ErrorResult) -> bool:
    """Reintentar solo fallos de forma/shape JSON atribuibles al modelo (paso 4)."""
    if err.error_type != ERROR_TYPE_INTERNAL:
        return False
    detail = (err.detail or "").lower()
    msg = (err.message or "").lower()
    if "reintentar" in detail:
        return True
    if "json" in msg or "inválid" in msg or "invalid" in msg:
        return True
    if "salida" in msg and "modelo" in msg:
        return True
    return False


def _build_success_result(
    *,
    rubric_markdown: str,
    validated_payload: dict,
    feedback_text: str,
    student_name: str,
    item_label: str | None,
    transcription: str | None,
    deliverable_kind: str,
    archivo_pdf: str | None,
) -> GradingResult:
    _ = rubric_markdown  # reserved for future rubric-grounded per-criterion ceilings
    rows = validated_payload["scores_by_criterion"]
    total_max = float(validated_payload.get("total_max_score") or 0.0)
    weights: list[float] = []
    for row in rows:
        try:
            weights.append(max(0.0, float(row.get("criterion_weight") or 0.0)))
        except (TypeError, ValueError):
            weights.append(0.0)
    sum_w = sum(weights)
    if sum_w <= 0.0 and rows:
        max_parts = [total_max / len(rows)] * len(rows)
    elif rows:
        max_parts = [(w / sum_w) * total_max for w in weights]
    else:
        max_parts = []

    scores: dict[str, CriterionScore] = {}
    for i, row in enumerate(rows):
        name = str(row["criterion_name"]).strip()
        max_s = max_parts[i] if i < len(max_parts) else 0.0
        scores[name] = CriterionScore(
            score=float(row["weighted_score"]),
            max_score=max_s,
            feedback="",
        )

    return GradingResult(
        scores_by_criterion=scores,
        total_score=float(validated_payload["total_weighted_score"]),
        total_max_score=float(validated_payload["total_max_score"]),
        feedback=feedback_text,
        student_name=student_name,
        item_label=item_label,
        transcription=transcription,
        deliverable_kind=deliverable_kind,
        archivo_pdf=archivo_pdf,
        status="success",
        rejection=None,
    )


class GradingPipeline:
    """
    Orquestador secuencial del flujo de calificación (**pasos 0–6**).

    **0** — Validación de ``GradingRequest`` (tipo de entrega y campos).
    **1** — Texto plano: parse JSON (texto), Whisper (audio) o PyMuPDF (PDF).
    **2** — Validación de contenido (regex + LLM opcional).
    **3** — Validación estructural mínima de la rúbrica.
    **4** — Calificación LLM (JSON ``scores_by_criterion``) con reintentos acotados.
    **5** — Validación determinística de la salida frente a la rúbrica.
    **6** — Generación de retroalimentación para el estudiante.
    """

    def __init__(
        self,
        *,
        transcription_service: TranscriptionService,
        pdf_extraction_service: PDFExtractionService,
        code_notebook_extraction_service: CodeNotebookExtractionService,
        plain_text_extraction_service: PlainTextExtractionService,
        content_validation: ContentValidationService,
        rubric_validation: RubricValidationService,
        grading: GradingService,
        output_validation: OutputValidationService,
        feedback: FeedbackService,
        research: RubricResearchService | None = None,
    ) -> None:
        """Wire all pipeline stages; callers typically use ``create_grading_pipeline``."""
        self._transcription = transcription_service
        self._pdf = pdf_extraction_service
        self._code_nb = code_notebook_extraction_service
        self._plain_text = plain_text_extraction_service
        self._content = content_validation
        self._rubric = rubric_validation
        self._grading = grading
        self._output = output_validation
        self._feedback = feedback
        self._research = research

    @property
    def research_service(self) -> RubricResearchService | None:
        """Expose the optional research service so HTTP handlers can reuse it."""
        return self._research

    def run(self, request: GradingRequest) -> GradingResult | ErrorResult:
        """
        Ejecuta los pasos 0–6 y devuelve ``GradingResult`` (éxito o rechazo estructurado)
        o ``ErrorResult`` ante fallos de validación o del modelo.
        """
        request_id = str(uuid.uuid4())
        _logger.info("grading_pipeline start request_id=%s", request_id)

        err = self._validate_request(request)
        if err is not None:
            return err

        delivery = request.delivery_type

        acquired = self._step1_acquire_text(request, request_id)
        if isinstance(acquired, ErrorResult):
            return acquired
        plain_text, item_question, archivo_path = acquired

        cv = self._content.validate(plain_text, request_id=request_id)
        if cv.verdict == "rejected":
            _logger.info(
                "grading_pipeline rejected request_id=%s layer=%s",
                request_id,
                cv.detection_layer,
            )
            return GradingResult(
                scores_by_criterion={},
                total_score=0.0,
                total_max_score=0.0,
                feedback="",
                student_name=request.student_name.strip(),
                item_label=(
                    item_question if delivery in (DeliveryType.TEXT, DeliveryType.AUDIO) else None
                ),
                transcription=plain_text if delivery == DeliveryType.AUDIO else None,
                deliverable_kind=delivery.value,
                archivo_pdf=archivo_path,
                status="rejected",
                rejection=GradingRejection(
                    rejection_reason=cv.reason,
                    warning_note=None,
                    flagged_patterns=tuple(cv.flagged_patterns),
                    detection_layer=cv.detection_layer,
                ),
            )

        rubric_err = self._rubric.validate(request.rubric_content, request_id=request_id)
        if rubric_err is not None:
            return rubric_err

        text_item_label: str | None = None
        if delivery in (DeliveryType.TEXT, DeliveryType.AUDIO):
            try:
                escala = escala_item_desde_rubrica(request.rubric_content, item_question)
                text_item_label = str(escala["item"])
            except ValueError as exc:
                return ErrorResult(
                    error_type=ERROR_TYPE_VALIDATION,
                    message=str(exc),
                    detail=None,
                )

        research_guide = self._resolve_research_guide(
            request.rubric_content, request_id=request_id
        )

        body_heading = _submission_body_heading(delivery, archivo_path or "")
        grading_out = self._step4_grade_with_json_retries(
            delivery=delivery,
            rubric=request.rubric_content,
            plain_text=plain_text,
            item_question=item_question,
            request_id=request_id,
            submission_body_heading=body_heading,
            research_guide=research_guide,
        )
        if isinstance(grading_out, ErrorResult):
            return grading_out

        allowed_names: tuple[str, ...] | None = None
        if delivery in (DeliveryType.TEXT, DeliveryType.AUDIO) and text_item_label is not None:
            allowed_names = (text_item_label,)

        validated = self._output.validate(
            grading_out,
            request.rubric_content,
            allowed_criterion_names=allowed_names,
            request_id=request_id,
        )
        if isinstance(validated, ErrorResult):
            return validated
        payload, _warnings = validated

        fb = self._feedback.generate_feedback(
            request.rubric_content,
            payload,
            request_id=request_id,
        )
        if isinstance(fb, ErrorResult):
            return fb

        transcription_field: str | None = plain_text if delivery == DeliveryType.AUDIO else None

        return _build_success_result(
            rubric_markdown=request.rubric_content,
            validated_payload=payload,
            feedback_text=fb,
            student_name=request.student_name.strip(),
            item_label=(
                text_item_label if delivery in (DeliveryType.TEXT, DeliveryType.AUDIO) else None
            ),
            transcription=transcription_field,
            deliverable_kind=delivery.value,
            archivo_pdf=archivo_path,
        )

    def _validate_request(self, request: object) -> ErrorResult | None:
        """Paso 0: tipo de entrega coercible y campos obligatorios no vacíos."""
        if not isinstance(request, GradingRequest):
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="La solicitud no es un GradingRequest válido.",
                detail=None,
            )
        coerced = _coerce_delivery_type(request.delivery_type)
        if isinstance(coerced, ErrorResult):
            return coerced
        request.delivery_type = coerced

        if not (request.student_name or "").strip():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El nombre del estudiante no puede estar vacío.",
                detail=None,
            )
        if not (request.rubric_content or "").strip():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="La rúbrica no puede estar vacía.",
                detail=None,
            )
        if not (request.content or "").strip():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El contenido de la entrega no puede estar vacío.",
                detail=None,
            )
        return None

    def _step1_acquire_text(
        self,
        request: GradingRequest,
        request_id: str,
    ) -> Union[tuple[str, str, str | None], ErrorResult]:
        """
        Paso 1: devuelve ``(texto_plano, pregunta_ítem, ruta_artifact_o_None)``.

        ``pregunta_ítem`` se usa en texto/audio. Para PDF o entrega de código (``.py`` /
        ``.ipynb``), el tercer campo es la ruta del archivo en disco usada para extracción
        y metadatos; para texto/audio es ``None``.
        """
        delivery = request.delivery_type
        if delivery == DeliveryType.TEXT:
            parsed = _parse_text_submission(request.content)
            if isinstance(parsed, ErrorResult):
                return parsed
            answer, question = parsed
            return answer, question, None

        if delivery == DeliveryType.AUDIO:
            parsed = _parse_audio_delivery(request.content, request.rubric_content)
            if isinstance(parsed, ErrorResult):
                return parsed
            audio_path, item_q = parsed
            out = self._transcription.transcribe(audio_path, request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            return out, item_q, None

        if delivery == DeliveryType.PDF_DELIVERABLE:
            out = self._pdf.extract(request.content.strip(), request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            path = request.content.strip()
            return out, "", path

        if delivery == DeliveryType.CODE_DELIVERABLE:
            out = self._code_nb.extract(request.content.strip(), request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            path = request.content.strip()
            return out, "", path

        if delivery == DeliveryType.PLAIN_TEXT_DELIVERABLE:
            out = self._plain_text.extract(request.content.strip(), request_id=request_id)
            if isinstance(out, ErrorResult):
                return out
            path = request.content.strip()
            return out, "", path

        return ErrorResult(
            error_type=ERROR_TYPE_VALIDATION,
            message="Tipo de entrega no soportado.",
            detail=str(delivery),
        )

    def _step4_grade_with_json_retries(
        self,
        *,
        delivery: DeliveryType,
        rubric: str,
        plain_text: str,
        item_question: str,
        request_id: str,
        submission_body_heading: str,
        research_guide: str | None = None,
    ) -> dict | ErrorResult:
        """
        Paso 4: invoca ``GradingService`` y reintenta hasta 3 veces ante fallos
        JSON/recuperables atribuibles al modelo.
        """
        last: ErrorResult | None = None
        for attempt in range(3):
            if delivery in (DeliveryType.TEXT, DeliveryType.AUDIO):
                out = self._grading.grade_text_item(
                    rubric,
                    item_question,
                    plain_text,
                    request_id=request_id,
                    research_guide=research_guide,
                )
            else:
                out = self._grading.grade_pdf_submission_text(
                    rubric,
                    plain_text,
                    request_id=request_id,
                    submission_body_heading=submission_body_heading,
                    research_guide=research_guide,
                )
            if isinstance(out, dict):
                if attempt:
                    _logger.info(
                        "grading_json succeeded request_id=%s after_attempt=%s",
                        request_id,
                        attempt + 1,
                    )
                return out
            last = out
            if not _grading_internal_recoverable(out):
                return out
            _logger.warning(
                "grading_json retry request_id=%s attempt=%s err=%s",
                request_id,
                attempt + 1,
                out.message,
            )
        assert last is not None
        return last

    def _resolve_research_guide(
        self,
        rubric_md: str,
        *,
        request_id: str,
    ) -> str | None:
        """Look up (or build) the rubric research guide; degrade gracefully on failure."""
        if self._research is None:
            return None
        try:
            cached = self._research.get_or_create(rubric_md, request_id=request_id)
        except Exception:
            _logger.warning(
                "research lookup raised request_id=%s; continuing without guide",
                request_id,
                exc_info=True,
            )
            return None
        if isinstance(cached, ErrorResult):
            _logger.info(
                "research unavailable request_id=%s err=%s",
                request_id,
                cached.message,
            )
            return None
        return cached.guide_markdown


__all__ = ["GradingPipeline"]
