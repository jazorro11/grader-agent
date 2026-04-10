import pytest

from grader_agent import transcription as transcription_module


def test_transcribir_audio_archivo_inexistente():
    with pytest.raises(ValueError, match="not found"):
        transcription_module.transcribir_audio("/no/existe/archivo.webm")
