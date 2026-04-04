# transcriber.py
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
            language="es"        # forzamos español para mejor precisión
        )
    return respuesta.text