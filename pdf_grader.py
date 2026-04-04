# pdf_grader.py
import fitz  # pymupdf
from openai import OpenAI
from dotenv import load_dotenv
import os, json

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CRITERIOS_IEEE = [
    "Resultados y Análisis Técnico",
    "Estructura e Hilo Conductor",
    "Formato IEEE e Imágenes"
]

SYSTEM_PROMPT_PDF = """
Sos un evaluador académico especializado en informes científicos con formato IEEE.

Recibirás:
1. Una RÚBRICA en formato Markdown con los criterios y puntajes máximos.
2. El TEXTO COMPLETO del informe del alumno extraído de un PDF.
3. El CRITERIO específico que debés evaluar en esta llamada.

Tu tarea:
- Evaluar el informe ÚNICAMENTE según el criterio indicado y la rúbrica provista.
- Si la rúbrica no menciona el criterio, respondé con puntaje 0 y explicá que no está en la rúbrica.
- Asignar un puntaje numérico entre 0 y el máximo indicado en la rúbrica.
- Justificar el puntaje citando EVIDENCIA TEXTUAL concreta del informe
  (frases o secciones específicas que respalden tu evaluación).
- Si el alumno demuestra comprensión aunque no use terminología exacta,
  otorgá al menos el 70% del puntaje de ese criterio.
- En caso de duda entre dos puntajes consecutivos, elegí el más alto.
- NO penalizar errores ortográficos salvo que la rúbrica lo indique.
- La retroalimentación debe ser un párrafo de 4-6 oraciones estructurado así:
  1. Fortalezas: qué hizo bien el alumno con evidencia textual concreta del informe.
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
  "retroalimentacion": "El informe presenta X (evidencia: '...'). Le faltó Y para el puntaje máximo."
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

def calificar_criterio(rubrica_md: str, texto_informe: str, criterio: str) -> dict:
    """
    Evalúa un criterio específico del informe con GPT-4o.
    Siempre requiere una rúbrica válida para funcionar.
    """
    user_message = f"""
RÚBRICA:
{rubrica_md}

CRITERIO A EVALUAR: {criterio}

TEXTO DEL INFORME:
{texto_informe}
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_PDF},
            {"role": "user",   "content": user_message}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)

def calificar_informe_completo(rubrica_md: str, ruta_pdf: str, nombre_alumno: str) -> dict:
    """
    Orquesta la calificación completa:
    extrae el texto, evalúa cada criterio y elimina el archivo temporal.
    """
    try:
        texto = extraer_texto_pdf(ruta_pdf)

        resultados_criterios = []
        total_obtenido = 0
        total_maximo   = 0

        for criterio in CRITERIOS_IEEE:
            resultado = calificar_criterio(rubrica_md, texto, criterio)
            resultados_criterios.append(resultado)
            total_obtenido += resultado["puntaje_obtenido"]
            total_maximo   += resultado["puntaje_maximo"]

        return {
            "alumno":         nombre_alumno,
            "tipo":           "informe_pdf",
            "criterios":      resultados_criterios,
            "total_obtenido": total_obtenido,
            "total_maximo":   total_maximo
        }

    finally:
        # elimina el PDF temporal sin importar si hubo error o no
        if os.path.exists(ruta_pdf):
            os.remove(ruta_pdf)