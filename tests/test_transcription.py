import pytest

from grader_agent import transcription as transcription_module


def test_transcribir_audio_archivo_inexistente():
    with pytest.raises(ValueError, match="no encontrado|inválido"):
        transcription_module.transcribir_audio("/no/existe/archivo.webm")
