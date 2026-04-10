"""Audio transcription via OpenAI speech-to-text."""

from __future__ import annotations

from pathlib import Path

from grader_agent.openai_client import get_openai_client
from grader_agent.openai_retry import with_openai_rate_limit_retry
from grader_agent.settings import transcription_language, transcription_model

client = get_openai_client()


def transcribir_audio(ruta_audio: str) -> str:
    """
    Transcribe an audio file using the configured speech model (default Whisper).

    Args:
        ruta_audio: Path to an audio file (e.g. .webm, .mp3, .wav).

    Returns:
        Transcript text.

    Raises:
        ValueError: if the path is missing or not a regular file.
    """
    path = Path(ruta_audio)
    if not path.is_file():
        raise ValueError(
            f"Audio file not found or is not a file: {ruta_audio}. "
            "Check the upload completed successfully."
        )

    def _transcribe():
        with path.open("rb") as archivo:
            return client.audio.transcriptions.create(
                model=transcription_model(),
                file=archivo,
                language=transcription_language(),
            )

    respuesta = with_openai_rate_limit_retry(_transcribe)
    text = getattr(respuesta, "text", None)
    if not isinstance(text, str) or not text.strip():
        raise ValueError(
            "The transcription service returned an empty result. "
            "Try a clearer recording or another format."
        )
    return text.strip()
