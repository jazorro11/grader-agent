import json
import os

import fitz  # pymupdf

from grader_agent.openai_client import get_openai_client
from grader_agent.prompts_loader import (
    system_prompt_pdf_evaluar_criterio,
    system_prompt_pdf_listar_criterios,
)

client = get_openai_client()


def extraer_texto_pdf(ruta_pdf: str) -> str:
    """
    Extrae el texto de un PDF de máximo 4 páginas.
    Lanza ValueError si el PDF excede ese límite.
    """
    doc = fitz.open(ruta_pdf)

    if len(doc) > 4:
        doc.close()
        raise ValueError(f"El PDF tiene {len(doc)} páginas. El máximo permitido es 4.")

    texto = ""
    for pagina in doc:
        texto += pagina.get_text()

    doc.close()
    return texto.strip()


def listar_criterios_desde_rubrica(rubrica_md: str) -> list[str]:
    """
    Usa el modelo para extraer los nombres de criterios evaluables de la rúbrica.
    Devuelve lista vacía si el JSON no es válido o no hay criterios.
    """
    user_message = f"RÚBRICA (Markdown):\n\n{rubrica_md}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_pdf_listar_criterios()},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    criterios = data.get("criterios")
    if not isinstance(criterios, list):
        return []
    out = []
    for c in criterios:
        if isinstance(c, str) and c.strip():
            out.append(c.strip())
    return out


def calificar_criterio_entregable(rubrica_md: str, texto_entregable: str, criterio: str) -> dict:
    """
    Evalúa un criterio específico del entregable con GPT-4o.
    """
    user_message = f"""
RÚBRICA:
{rubrica_md}

CRITERIO A EVALUAR: {criterio}

TEXTO DEL ENTREGABLE:
{texto_entregable}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_pdf_evaluar_criterio()},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    return json.loads(response.choices[0].message.content)


def calificar_entregable_pdf(rubrica_md: str, ruta_pdf: str, nombre_alumno: str) -> dict:
    """
    Extrae el texto del PDF, lista criterios desde la rúbrica, evalúa cada uno y elimina el temporal.
    """
    try:
        texto = extraer_texto_pdf(ruta_pdf)
        criterios = listar_criterios_desde_rubrica(rubrica_md)
        if not criterios:
            raise ValueError(
                "No se identificaron criterios evaluables en la rúbrica. "
                "Revisá que el .md describa ítems o criterios con puntaje."
            )

        resultados_criterios = []
        total_obtenido = 0
        total_maximo = 0

        for criterio in criterios:
            resultado = calificar_criterio_entregable(rubrica_md, texto, criterio)
            resultados_criterios.append(resultado)
            total_obtenido += resultado["puntaje_obtenido"]
            total_maximo += resultado["puntaje_maximo"]

        return {
            "alumno": nombre_alumno,
            "tipo": "entregable_pdf",
            "criterios": resultados_criterios,
            "total_obtenido": total_obtenido,
            "total_maximo": total_maximo,
        }

    finally:
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)
