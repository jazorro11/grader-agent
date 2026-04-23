"""Audio transcription via OpenAI speech-to-text."""

from __future__ import annotations

from grader_agent.llm.clients import get_default_openai_transcription_client
from grader_agent.models import ErrorResult
from grader_agent.services.transcription import TranscriptionService


def transcribir_audio(ruta_audio: str) -> str:
    """
    Transcribe an audio file using the configured speech model (default Whisper).

    Args:
        ruta_audio: Path to an audio file (e.g. .webm, .mp3, .wav).

    Returns:
        Transcript text.

    Raises:
        ValueError: if the path is missing, invalid, over size limit, or transcription fails.
    """
    client = get_default_openai_transcription_client()
    svc = TranscriptionService(client)
    out = svc.transcribe(ruta_audio)
    if isinstance(out, ErrorResult):
        raise ValueError(out.message)
    return out
