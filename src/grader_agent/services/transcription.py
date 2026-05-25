"""3.1 — Audio transcription service (Whisper-compatible validation)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Union

from grader_agent.models import ERROR_TYPE_OPENAI, ERROR_TYPE_VALIDATION, ErrorResult
from grader_agent.openai_retry import with_transient_api_retry
from grader_agent.settings import transcription_language, transcription_model

if TYPE_CHECKING:
    from openai import OpenAI

_logger = logging.getLogger(__name__)

_WHISPER_MAX_BYTES = 25 * 1024 * 1024

# OpenAI speech-to-text supported containers/extensions (subset explicitly allowed here).
_WHISPER_SUFFIXES = frozenset(
    {
        ".flac",
        ".m4a",
        ".mp3",
        ".mp4",
        ".mpeg",
        ".mpga",
        ".oga",
        ".ogg",
        ".wav",
        ".webm",
    }
)


class TranscriptionService:
    """
    Transcribe audio via OpenAI Whisper (or compatible ``audio.transcriptions`` API).

    The OpenAI client is injected (tests and alternate hosts).
    """

    def __init__(self, openai_client: OpenAI) -> None:
        """``openai_client`` should target ``api.openai.com`` (Whisper), not OpenRouter."""
        self._client = openai_client

    def transcribe(
        self, audio_path: str, *, request_id: str | None = None
    ) -> Union[str, ErrorResult]:
        """
        Paso 1 (audio): valida ruta, formato, tamaño y llama ``audio.transcriptions.create``.

        Returns:
            Texto transcrito o ``ErrorResult``.
        """
        path = Path(audio_path)
        if not path.is_file():
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="Archivo de audio no encontrado o inválido.",
                detail=str(audio_path),
            )

        suffix = path.suffix.lower()
        if suffix not in _WHISPER_SUFFIXES:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message=(
                    "Formato de audio no compatible con el motor de transcripción. "
                    f"Usá uno de: {', '.join(sorted(_WHISPER_SUFFIXES))}."
                ),
                detail=suffix or "(sin extensión)",
            )

        try:
            size = path.stat().st_size
        except OSError as exc:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="No se pudo leer el archivo de audio.",
                detail=str(exc),
            )

        if size > _WHISPER_MAX_BYTES:
            return ErrorResult(
                error_type=ERROR_TYPE_VALIDATION,
                message="El audio supera el máximo permitido de 25 MB.",
                detail=f"{size} bytes",
            )

        def _call():
            with path.open("rb") as fh:
                return self._client.audio.transcriptions.create(
                    model=transcription_model(),
                    file=fh,
                    language=transcription_language(),
                )

        if request_id:
            _logger.debug("transcription request_id=%s path=%s", request_id, audio_path)
        try:
            respuesta = with_transient_api_retry(_call, max_attempts=3)
        except Exception as exc:  # OpenAIError or network
            _logger.exception("Transcription API failed")
            return ErrorResult(
                error_type=ERROR_TYPE_OPENAI,
                message="El servicio de transcripción falló o no está disponible.",
                detail=str(exc),
            )

        text = getattr(respuesta, "text", None)
        if not isinstance(text, str) or not text.strip():
            return ErrorResult(
                error_type=ERROR_TYPE_OPENAI,
                message="La transcripción devolvió un resultado vacío.",
                detail=None,
            )
        return text.strip()


__all__ = ["TranscriptionService"]
