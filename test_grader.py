# test_grader.py
from grader import calificar_respuesta

rubrica = """
## Pregunta 1 — Sistemas operativos (10 puntos)
**Respuesta esperada:** Un sistema operativo gestiona los recursos del hardware 
y provee servicios a los programas. Ejemplos: Windows, Linux, macOS.
"""

respuesta = "El sistema operativo es el software que administra el hardware y permite correr aplicaciones"

resultado = calificar_respuesta(rubrica, "Pregunta 1", respuesta)
print(resultado)