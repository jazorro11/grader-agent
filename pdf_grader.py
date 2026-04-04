# pdf_grader.py
import fitz  # pymupdf
from openai import OpenAI
from dotenv import load_dotenv
import json
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT_LISTAR_CRITERIOS = """
Sos un asistente que analiza rúbricas académicas en Markdown.

Tu tarea:
- Identificar únicamente los CRITERIOS DE EVALUACIÓN o ítems que deben calificarse con puntaje.
- Usar el nombre tal como aparece en la rúbrica (título del criterio o pregunta evaluable).
- NO incluir: escalas generales de valoración, introducciones, tablas solo descriptivas,
  secciones de referencias o bibliografía, anexos sin puntaje, ni duplicados.
- NO inventar criterios que no estén implícitos o explícitos en el texto.
- Si no hay criterios evaluables claros, devolvé una lista vacía.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto:
{"criterios": ["nombre 1", "nombre 2"]}
"""

SYSTEM_PROMPT_ENTREGABLE = """
Sos un evaluador académico riguroso y justo.

Recibirás:
1. Una RÚBRICA en formato Markdown con criterios y puntajes máximos.
2. El TEXTO COMPLETO del entregable del alumno extraído de un PDF.
3. El CRITERIO específico que debés evaluar en esta llamada.

Tu tarea:
- Evaluar el entregable ÚNICAMENTE según el criterio indicado y la rúbrica provista.
- Si la rúbrica no menciona el criterio, respondé con puntaje 0 y explicá que no está en la rúbrica.
- Asignar un puntaje numérico entre 0 y el máximo indicado en la rúbrica para ese criterio.
- Justificar el puntaje citando EVIDENCIA TEXTUAL concreta del entregable
  (frases o secciones específicas que respalden tu evaluación).
- Si el alumno demuestra comprensión aunque no use terminología exacta,
  otorgá al menos el 70% del puntaje de ese criterio.
- En caso de duda entre dos puntajes consecutivos, elegí el más alto.
- NO penalizar errores ortográficos salvo que la rúbrica lo indique.
- La retroalimentación debe ser un párrafo de 4-6 oraciones estructurado así:
  1. Fortalezas: qué hizo bien el alumno con evidencia textual concreta del entregable.
  2. Debilidades: qué aspectos están ausentes, incompletos o mal desarrollados.
  3. Justificación del puntaje: explica explícitamente por qué se asignó ese puntaje
     y no el máximo, conectando las debilidades con los criterios de la rúbrica.

IMPORTANTE: No uses conocimiento externo ni criterios propios.
Evaluá SOLO con lo que dice la rúbrica. Si algo no está en la rúbrica, no lo penalices.

Respondé ÚNICAMENTE con un objeto JSON con este formato exacto, sin texto adicional:
{
  "criterio": "nombre del criterio evaluado",
  "puntaje_obtenido": 7,
  "puntaje_maximo": 10,
  "retroalimentacion": "El entregable presenta X (evidencia: '...'). Le faltó Y para el puntaje máximo."
}
"""


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
            {"role": "system", "content": SYSTEM_PROMPT_LISTAR_CRITERIOS},
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
            {"role": "system", "content": SYSTEM_PROMPT_ENTREGABLE},
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