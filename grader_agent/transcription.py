from grader_agent.openai_client import get_openai_client

client = get_openai_client()


def transcribir_audio(ruta_audio: str) -> str:
    """
    Transcribe un archivo de audio usando Whisper.

    Args:
        ruta_audio: path al archivo de audio (.mp3, .wav, .m4a, .webm)

    Returns:
        texto transcripto como string
    """
    with open(ruta_audio, "rb") as archivo:
        respuesta = client.audio.transcriptions.create(
            model="whisper-1",
            file=archivo,
            language="es",
        )
    return respuesta.text
