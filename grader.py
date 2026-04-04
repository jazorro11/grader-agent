# grader.py
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Sos un asistente de calificación académica estricto y justo.

Recibirás:
1. Una RÚBRICA en formato Markdown con las preguntas, respuestas esperadas y puntaje máximo.
2. La RESPUESTA DE UN ALUMNO para una pregunta específica.

Tu tarea:
- Comparar la respuesta del alumno con la respuesta esperada.
- Asignar un puntaje numérico entre 0 y el máximo indicado.
- Ser flexible con sinónimos, parafraseos y respuestas parcialmente correctas.
- NO penalizar errores ortográficos o gramaticales salvo que la rúbrica lo indique.
- Si el alumno demuestra comprensión del concepto aunque no use la terminología exacta,
  otorgá al menos el 70% del puntaje de ese criterio.
- En caso de duda entre dos puntajes consecutivos, elegí el más alto.
- Escribir una retroalimentación breve (2-3 oraciones) explicando qué hizo bien
  el alumno y qué le faltó para obtener el puntaje máximo.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto, sin texto adicional:
{
  "pregunta": "nombre o número de la pregunta",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "Identificó correctamente X. Faltó desarrollar Y."
}
"""

def calificar_respuesta(rubrica_md: str, pregunta: str, respuesta_alumno: str) -> dict:
    user_message = f"""
RÚBRICA:
{rubrica_md}

PREGUNTA A CALIFICAR: {pregunta}

RESPUESTA DEL ALUMNO: {respuesta_alumno}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    import json
    return json.loads(response.choices[0].message.content)