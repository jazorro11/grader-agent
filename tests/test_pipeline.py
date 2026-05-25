"""Fase 4: ``GradingPipeline`` (orquestación sin LLM real salvo donde se mockea)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from grader_agent.models import (
    ERROR_TYPE_INTERNAL,
    ERROR_TYPE_RUBRIC,
    ERROR_TYPE_VALIDATION,
    ContentValidationResult,
    DeliveryType,
    ErrorResult,
    GradingRequest,
    GradingResult,
)
from grader_agent.pipeline import GradingPipeline, _submission_body_heading


def _minimal_rubric() -> str:
    return "# Actividad\n\nCriterio 25%\n"


def _make_pipeline(**overrides: object) -> GradingPipeline:
    defaults = {
        "transcription_service": MagicMock(),
        "pdf_extraction_service": MagicMock(),
        "code_notebook_extraction_service": MagicMock(),
        "content_validation": MagicMock(),
        "rubric_validation": MagicMock(),
        "grading": MagicMock(),
        "output_validation": MagicMock(),
        "feedback": MagicMock(),
    }
    defaults.update(overrides)
    return GradingPipeline(**defaults)  # type: ignore[arg-type]


def test_step0_rejects_non_dataclass() -> None:
    pipe = _make_pipeline()
    out = pipe.run("not-a-request")  # type: ignore[arg-type]
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_step0_rejects_plain_text_delivery_content() -> None:
    pipe = _make_pipeline()
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content="solo texto sin json",
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_step2_regex_rejection_returns_grading_result() -> None:
    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="rejected",
        reason="regex",
        flagged_patterns=("instruction_override",),
        detection_layer="regex",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "Respuesta válida."}',
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)
    assert isinstance(out, GradingResult)
    assert out.status == "rejected"
    assert out.rejection is not None
    assert out.rejection.detection_layer == "regex"
    rubric_validation.validate.assert_not_called()


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_success_text_path(mock_escala: MagicMock) -> None:
    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "Item1",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()
    grading.grade_text_item.return_value = grading_payload

    validated = (
        {
            "scores_by_criterion": grading_payload["scores_by_criterion"],
            "total_weighted_score": 8.0,
            "total_max_score": 10.0,
        },
        [],
    )
    output_validation = MagicMock()
    output_validation.validate.return_value = validated

    feedback = MagicMock()
    feedback.generate_feedback.return_value = "Muy bien."

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "Mi respuesta."}',
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)
    assert isinstance(out, GradingResult)
    assert out.status == "success"
    assert out.total_score == 8.0
    assert "Item1" in out.scores_by_criterion
    grading.grade_text_item.assert_called_once()
    kwargs = grading.grade_text_item.call_args.kwargs
    assert "request_id" in kwargs and kwargs["request_id"]


def test_success_code_deliverable_extract_and_grade_heading(tmp_path: object) -> None:
    path = tmp_path / "t.py"
    path.write_text("a = 1\n", encoding="utf-8")

    code_nb = MagicMock()
    code_nb.extract.return_value = "a = 1\n"
    pdf_ex = MagicMock()

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "Criterio 25%",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()
    grading.grade_pdf_submission_text.return_value = grading_payload

    validated = (
        {
            "scores_by_criterion": grading_payload["scores_by_criterion"],
            "total_weighted_score": 8.0,
            "total_max_score": 10.0,
        },
        [],
    )
    output_validation = MagicMock()
    output_validation.validate.return_value = validated

    feedback = MagicMock()
    feedback.generate_feedback.return_value = "Bien."

    pipe = _make_pipeline(
        pdf_extraction_service=pdf_ex,
        code_notebook_extraction_service=code_nb,
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.CODE_DELIVERABLE,
        content=str(path),
        student_name="Bob",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)
    assert isinstance(out, GradingResult)
    assert out.status == "success"
    code_nb.extract.assert_called_once()
    pdf_ex.extract.assert_not_called()
    grading.grade_pdf_submission_text.assert_called_once()
    heading = grading.grade_pdf_submission_text.call_args.kwargs["submission_body_heading"]
    assert "PYTHON" in heading.upper()


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_step4_retries_internal_json_error(mock_escala: MagicMock) -> None:
    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="llm",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    bad = ErrorResult(
        error_type=ERROR_TYPE_INTERNAL,
        message="JSON inválido.",
        detail="Reintentar la calificación.",
    )
    ok = {
        "scores_by_criterion": [
            {
                "criterion_name": "Item1",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()
    grading.grade_text_item.side_effect = [bad, ok]

    output_validation = MagicMock()
    output_validation.validate.return_value = (ok, [])

    feedback = MagicMock()
    feedback.generate_feedback.return_value = "Ok."

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "R."}',
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)
    assert isinstance(out, GradingResult)
    assert grading.grade_text_item.call_count == 2


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_audio_uses_transcription(mock_escala: MagicMock) -> None:
    mock_escala.return_value = {"item": "C1", "puntaje_maximo": 5.0, "niveles": None}

    transcription = MagicMock()
    transcription.transcribe.return_value = "hola audio"

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "C1",
                "criterion_weight": 100.0,
                "level_obtained": "1",
                "level_percentage": 50.0,
                "weighted_score": 2.5,
            }
        ],
        "total_weighted_score": 2.5,
        "total_max_score": 5.0,
    }
    grading = MagicMock()
    grading.grade_text_item.return_value = grading_payload

    output_validation = MagicMock()
    output_validation.validate.return_value = (grading_payload, [])
    feedback = MagicMock()
    feedback.generate_feedback.return_value = "Bien."

    pipe = _make_pipeline(
        transcription_service=transcription,
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.AUDIO,
        content=r'{"path": "C:\\fake\\audio.mp3", "pregunta": "P1"}',
        student_name="Bob",
        rubric_content="# R\n\n10%\n\n## C1\nmax 5\n",
    )
    out = pipe.run(req)
    assert isinstance(out, GradingResult)
    transcription.transcribe.assert_called_once()
    grading.grade_text_item.assert_called_once()
    assert out.transcription == "hola audio"


def test_rubric_validation_error_short_circuits_grading() -> None:
    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = ErrorResult(
        error_type=ERROR_TYPE_RUBRIC,
        message="Falta porcentaje en la rúbrica.",
        detail=None,
    )
    grading = MagicMock()

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "ok"}',
        student_name="Ana",
        rubric_content="# Actividad\n\nSin porcentajes aqui\n",
    )
    out = pipe.run(req)

    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_RUBRIC
    grading.grade_text_item.assert_not_called()


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_successful_text_run_order_content_before_rubric_before_grading(
    mock_escala: MagicMock,
) -> None:
    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}

    order: list[str] = []

    content_validation = MagicMock()

    def _cv(*args: object, **kwargs: object) -> ContentValidationResult:
        order.append("content")
        return ContentValidationResult(
            verdict="clean",
            reason="ok",
            flagged_patterns=(),
            detection_layer="regex_only",
        )

    content_validation.validate.side_effect = _cv

    rubric_validation = MagicMock()

    def _rv(*args: object, **kwargs: object) -> None:
        order.append("rubric")
        return None

    rubric_validation.validate.side_effect = _rv

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "Item1",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()

    def _grade(*args: object, **kwargs: object) -> dict:
        order.append("grading")
        return grading_payload

    grading.grade_text_item.side_effect = _grade

    output_validation = MagicMock()
    output_validation.validate.return_value = (grading_payload, [])
    feedback = MagicMock()
    feedback.generate_feedback.return_value = "Ok."

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "R."}',
        student_name="Ana",
        rubric_content="# Actividad\n\n25%\n",
    )
    out = pipe.run(req)

    assert isinstance(out, GradingResult)
    assert order == ["content", "rubric", "grading"]
    output_validation.validate.assert_called_once()
    feedback.generate_feedback.assert_called_once()


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_internal_non_recoverable_error_returns_error_result_shape(
    mock_escala: MagicMock,
) -> None:
    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading = MagicMock()
    grading.grade_text_item.return_value = ErrorResult(
        error_type=ERROR_TYPE_INTERNAL,
        message="Fallo permanente.",
        detail="sin reintentos",
    )

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "R."}',
        student_name="Ana",
        rubric_content="# Actividad\n\n25%\n",
    )
    out = pipe.run(req)

    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_INTERNAL
    assert out.message
    grading.grade_text_item.assert_called_once()


def test_submission_body_heading_pdf_vs_docx() -> None:
    assert _submission_body_heading(DeliveryType.PDF_DELIVERABLE, r"C:\tmp\informe.docx") == (
        "TEXTO PLANO DEL ENTREGABLE (DOCX)"
    )
    assert _submission_body_heading(DeliveryType.PDF_DELIVERABLE, "x.PDF") == "TEXTO PLANO DEL ENTREGABLE (PDF)"


@patch("grader_agent.pipeline.escala_item_desde_rubrica")
def test_research_guide_injected_into_grading_call(mock_escala: MagicMock) -> None:
    from grader_agent.services.research_cache import CachedResearch

    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}

    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "Item1",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()
    grading.grade_text_item.return_value = grading_payload
    output_validation = MagicMock()
    output_validation.validate.return_value = (grading_payload, [])
    feedback = MagicMock()
    feedback.generate_feedback.return_value = "ok"

    research_service = MagicMock()
    research_service.get_or_create.return_value = CachedResearch(
        rubric_hash="abc",
        guide_markdown="# Guía de investigación\n## Tema X\n- Hecho: contenido.",
        payload={"temas": [{"tema": "Tema X"}]},
    )

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
        research=research_service,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "R."}',
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    out = pipe.run(req)

    assert isinstance(out, GradingResult)
    grading.grade_text_item.assert_called_once()
    kwargs = grading.grade_text_item.call_args.kwargs
    assert "research_guide" in kwargs
    assert "Tema X" in kwargs["research_guide"]
    research_service.get_or_create.assert_called_once()


def test_research_failure_continues_grading_without_guide() -> None:
    content_validation = MagicMock()
    content_validation.validate.return_value = ContentValidationResult(
        verdict="clean",
        reason="ok",
        flagged_patterns=(),
        detection_layer="regex_only",
    )
    rubric_validation = MagicMock()
    rubric_validation.validate.return_value = None

    grading_payload = {
        "scores_by_criterion": [
            {
                "criterion_name": "Item1",
                "criterion_weight": 100.0,
                "level_obtained": "Nivel 2",
                "level_percentage": 80.0,
                "weighted_score": 8.0,
            }
        ],
        "total_weighted_score": 8.0,
        "total_max_score": 10.0,
    }
    grading = MagicMock()
    grading.grade_text_item.return_value = grading_payload
    output_validation = MagicMock()
    output_validation.validate.return_value = (grading_payload, [])
    feedback = MagicMock()
    feedback.generate_feedback.return_value = "ok"

    research_service = MagicMock()
    research_service.get_or_create.return_value = ErrorResult(
        error_type=ERROR_TYPE_INTERNAL,
        message="research deshabilitado",
        detail=None,
    )

    pipe = _make_pipeline(
        content_validation=content_validation,
        rubric_validation=rubric_validation,
        grading=grading,
        output_validation=output_validation,
        feedback=feedback,
        research=research_service,
    )
    req = GradingRequest(
        delivery_type=DeliveryType.TEXT,
        content='{"pregunta": "P1", "respuesta": "R."}',
        student_name="Ana",
        rubric_content=_minimal_rubric(),
    )
    with patch("grader_agent.pipeline.escala_item_desde_rubrica") as mock_escala:
        mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}
        out = pipe.run(req)

    assert isinstance(out, GradingResult)
    kwargs = grading.grade_text_item.call_args.kwargs
    assert kwargs.get("research_guide") is None
