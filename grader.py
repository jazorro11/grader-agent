# grader.py
from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
Sos un asistente de calificación académica estricto y justo.

Recibirás:
1. Una RÚBRICA en formato Markdown (preguntas, descriptores, respuestas esperadas, puntaje máximo).
2. La RESPUESTA DE UN ALUMNO para una pregunta o ítem específico que el docente indicó.

Tu tarea:
- Calificar usando solo la rúbrica: localizá el ítem que corresponde a esa pregunta y sus descriptores.
- Asignar un puntaje numérico entre 0 y el máximo indicado en la rúbrica para ese ítem.
- Ser flexible con sinónimos, parafraseos y respuestas parcialmente correctas.
- NO penalizar errores ortográficos o gramaticales salvo que la rúbrica lo indique.
- Si el alumno demuestra comprensión aunque no use la terminología exacta,
  otorgá al menos el 70% del puntaje de ese criterio.
- En caso de duda entre dos puntajes consecutivos, elegí el más alto.

Retroalimentación (obligatorio, no genérica):
- Entre 3 y 5 oraciones, en tono humano y respetuoso.
- CITÁ ideas, datos o frases concretas de la respuesta del alumno (podés parafrasear entre comillas).
- Conectá explícitamente con el descriptor o nivel de la rúbrica que aplicás (sin inventar criterios).
- PROHIBIDO usar frases vacías sin anclaje: "muy bien en general", "buen trabajo", "correcto"
  sin decir qué y por qué según la rúbrica.
- Explicá qué faltaría o qué mejoraría para alcanzar el puntaje máximo, de forma concreta.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto, sin texto adicional:
{
  "pregunta": "nombre o número de la pregunta",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "Texto concreto anclado a la respuesta y a la rúbrica."
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

    return json.loads(response.choices[0].message.content)