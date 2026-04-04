import json

from grader_agent.openai_client import get_openai_client
from grader_agent.prompts_loader import system_prompt_texto_item

client = get_openai_client()


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
            {"role": "system", "content": system_prompt_texto_item()},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)
