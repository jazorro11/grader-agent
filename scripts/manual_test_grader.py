# Script manual de integración: llama a la API real de OpenAI.
# Requiere OPENAI_API_KEY en el entorno. No forma parte de la suite pytest.
# Uso (desde la raíz del repo): venv\Scripts\python scripts\manual_test_grader.py

from grader import calificar_respuesta

rubrica = """
## Pregunta 1 — Sistemas operativos (10 puntos)
**Respuesta esperada:** Un sistema operativo gestiona los recursos del hardware
y provee servicios a los programas. Ejemplos: Windows, Linux, macOS.
"""

respuesta = (
    "El sistema operativo es el software que administra el hardware "
    "y permite correr aplicaciones"
)


def main() -> None:
    resultado = calificar_respuesta(rubrica, "Pregunta 1", respuesta)
    print(resultado)


if __name__ == "__main__":
    main()
