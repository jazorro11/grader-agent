"""Fase 7.1 — rutas explícitas OpenRouter (chat) vs OpenAI directo (Whisper)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.grading_pipeline_factory import create_grading_pipeline
from grader_agent.services.grading import GradingService
from grader_agent.services.transcription import TranscriptionService


@patch("app.grading_pipeline_factory.make_openrouter_chat_client")
@patch("app.grading_pipeline_factory.make_openai_transcription_client")
def test_factory_injects_separate_clients(mock_openai_factory, mock_router_factory) -> None:
    chat = MagicMock(name="openrouter_chat_client")
    whisper = MagicMock(name="openai_whisper_client")
    mock_router_factory.return_value = chat
    mock_openai_factory.return_value = whisper

    pipe = create_grading_pipeline()

    assert pipe._transcription._client is whisper  # type: ignore[attr-defined]
    assert pipe._grading._client is chat  # type: ignore[attr-defined]
    assert pipe._content._llm._client is chat  # type: ignore[attr-defined]
    mock_router_factory.assert_called_once()
    mock_openai_factory.assert_called_once()
    assert mock_router_factory.call_args != mock_openai_factory.call_args


@patch("grader_agent.services.grading.chat_completion_json_content")
@patch("grader_agent.services.grading.escala_item_desde_rubrica")
def test_grading_service_routes_chat_through_injected_openrouter(
    mock_escala: MagicMock,
    mock_chat_json: MagicMock,
) -> None:
    """La llamada principal de calificación usa el cliente OpenRouter inyectado en el servicio."""
    router = MagicMock(name="router")
    mock_escala.return_value = {"item": "Item1", "puntaje_maximo": 10.0, "niveles": None}
    mock_chat_json.return_value = (
        '{"scores_by_criterion": ['
        '{"criterion_name": "Item1", "criterion_weight": 100, '
        '"level_obtained": "Nivel 3", "level_percentage": 75, "weighted_score": 7.5}'
        "], "
        '"total_weighted_score": 7.5, "total_max_score": 10}'
    )

    svc = GradingService(router)
    out = svc.grade_text_item("# R\n\n## Item1\n\n100%\n", "Item1", "Respuesta breve.")

    assert isinstance(out, dict)
    assert "scores_by_criterion" in out
    mock_chat_json.assert_called_once()
    assert mock_chat_json.call_args.args[0] is router


def test_transcription_uses_openai_audio_api_not_chat(tmp_path) -> None:
    wav = tmp_path / "clip.wav"
    wav.write_bytes(b"dummy-bytes")

    openai = MagicMock()
    openai.audio.transcriptions.create.return_value = MagicMock(text="transcrito")

    svc = TranscriptionService(openai)

    def _immediate(fn, **_kwargs):
        return fn()

    with patch(
        "grader_agent.services.transcription.with_transient_api_retry",
        side_effect=_immediate,
    ):
        out = svc.transcribe(str(wav))

    assert out == "transcrito"
    openai.audio.transcriptions.create.assert_called_once()
    openai.chat.completions.create.assert_not_called()
