# Script manual de integración: transcribe con Whisper (API real).
# Requiere OPENAI_API_KEY y un archivo de audio. No forma parte de pytest.
# Uso: venv\Scripts\python scripts\manual_test_transcriber.py

from transcriber import transcribir_audio


def main() -> None:
    texto = transcribir_audio("Test.mp3")  # cambiá el nombre por el tuyo
    print(texto)


if __name__ == "__main__":
    main()
