import json
import os

import fitz  # pymupdf

from grader_agent.grading.llm_json import json_object_from_message_content
from grader_agent.grading.rubric_blocks import bloque_niveles_usuario
from grader_agent.grading.score_utils import ajustar_puntaje_a_niveles_discretos
from grader_agent.grading_config import (
    chat_completion_limit_kwargs,
    retro_temperature,
    score_temperature,
)
from grader_agent.openai_client import get_openai_client
from grader_agent.prompts_loader import (
    system_prompt_pdf_listar_criterios,
    system_prompt_pdf_puntaje_criterio,
    system_prompt_pdf_retro_criterio,
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


def _parse_metadatos_criterios_payload(data: dict) -> list[dict]:
    raw = data.get("criterios")
    if not isinstance(raw, list):
        return []
    out: list[dict] = []
    for item in raw:
        if isinstance(item, str):
            continue
        if not isinstance(item, dict):
            continue
        name = item.get("criterio")
        if not isinstance(name, str) or not name.strip():
            continue
        try:
            mx = float(item["puntaje_maximo"])
        except (KeyError, TypeError, ValueError):
            continue
        if mx <= 0:
            continue
        entry: dict = {"criterio": name.strip(), "puntaje_maximo": mx}
        niveles = item.get("niveles")
        if isinstance(niveles, list) and niveles:
            cleaned = []
            for n in niveles:
                if not isinstance(n, dict):
                    continue
                try:
                    pto = float(n["puntos"])
                except (KeyError, TypeError, ValueError):
                    continue
                etq = n.get("etiqueta")
                etiqueta = str(etq).strip() if etq is not None else ""
                cleaned.append({"etiqueta": etiqueta, "puntos": pto})
            if cleaned:
                entry["niveles"] = cleaned
        out.append(entry)
    return out


def metadatos_criterios_desde_rubrica(rubrica_md: str) -> list[dict]:
    """
    Extrae criterios evaluables con puntaje máximo canónico (y niveles opcionales) desde la rúbrica.
    """
    user_message = f"RÚBRICA (md):\n\n{rubrica_md}"
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_pdf_listar_criterios()},
            {"role": "user", "content": user_message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
        **chat_completion_limit_kwargs(kind="listar"),
    )
    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return _parse_metadatos_criterios_payload(data)


def listar_criterios_desde_rubrica(rubrica_md: str) -> list[str]:
    """
    Nombres de criterios evaluables (fachada sobre metadatos_criterios_desde_rubrica).
    """
    return [m["criterio"] for m in metadatos_criterios_desde_rubrica(rubrica_md)]


def calificar_criterio_entregable(
    rubrica_md: str,
    texto_entregable: str,
    criterio: str,
    puntaje_maximo: float,
    *,
    niveles: list[dict] | None = None,
) -> dict:
    """
    Evalúa un criterio: puntaje con temperatura baja y retro con temperatura más alta.
    El puntaje máximo es canónico (no lo devuelve el modelo).
    """
    bloque_n = bloque_niveles_usuario(niveles)
    user_puntaje = f"""RÚBRICA:
{rubrica_md}

CRITERIO: {criterio}
MÁX canónico (techo; no reinterpretes; el sistema fija el máximo en salida): {puntaje_maximo}
{bloque_n}ENTREGABLE:
{texto_entregable}
"""

    r_p = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_pdf_puntaje_criterio()},
            {"role": "user", "content": user_puntaje},
        ],
        temperature=score_temperature(),
        response_format={"type": "json_object"},
        **chat_completion_limit_kwargs(kind="puntaje"),
    )
    raw_p = r_p.choices[0].message.content
    data_p = json_object_from_message_content(raw_p)
    try:
        bruto = float(data_p.get("puntaje_obtenido", 0))
    except (TypeError, ValueError):
        bruto = 0.0
    puntaje_obtenido = ajustar_puntaje_a_niveles_discretos(bruto, niveles, puntaje_maximo)

    user_retro = f"""RÚBRICA:
{rubrica_md}

CRITERIO: {criterio}
PUNTAJE fijo: {puntaje_obtenido}/{puntaje_maximo}

ENTREGABLE:
{texto_entregable}
"""

    r_r = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt_pdf_retro_criterio()},
            {"role": "user", "content": user_retro},
        ],
        temperature=retro_temperature(),
        response_format={"type": "json_object"},
        **chat_completion_limit_kwargs(kind="retro"),
    )
    raw_r = r_r.choices[0].message.content
    data_r = json_object_from_message_content(raw_r)
    retro = data_r.get("retroalimentacion")
    if not isinstance(retro, str):
        retro = ""

    return {
        "criterio": criterio,
        "puntaje_obtenido": puntaje_obtenido,
        "puntaje_maximo": puntaje_maximo,
        "retroalimentacion": retro,
    }


def calificar_entregable_pdf(
    rubrica_md: str,
    ruta_pdf: str,
    nombre_alumno: str,
    *,
    criterios: list[str] | None = None,
    metadatos_criterios: list[dict] | None = None,
) -> dict:
    """
    Extrae el texto del PDF, obtiene metadatos de criterios (salvo que vengan precargados),
    evalúa cada uno y elimina el temporal.
    """
    try:
        texto = extraer_texto_pdf(ruta_pdf)
        meta = metadatos_criterios
        if meta is None:
            meta = metadatos_criterios_desde_rubrica(rubrica_md)
        if not meta:
            raise ValueError(
                "No se identificaron criterios evaluables en la rúbrica. "
                "Revisá que el .md describa ítems o criterios con puntaje."
            )
        if criterios is not None:
            if not criterios:
                raise ValueError(
                    "No se identificaron criterios evaluables en la rúbrica. "
                    "Revisá que el .md describa ítems o criterios con puntaje."
                )
            by_name = {m["criterio"]: m for m in meta}
            ordered: list[dict] = []
            for name in criterios:
                if name not in by_name:
                    raise ValueError(
                        f"No se halló el criterio «{name}» en la rúbrica parseada. "
                        "Verificá que el nombre coincida con el del .md."
                    )
                ordered.append(by_name[name])
            meta = ordered

        resultados_criterios = []
        total_obtenido = 0.0
        total_maximo = 0.0

        for m in meta:
            criterio = m["criterio"]
            pmax = float(m["puntaje_maximo"])
            niveles = m.get("niveles")
            if isinstance(niveles, list) and not niveles:
                niveles = None
            elif not isinstance(niveles, list):
                niveles = None
            resultado = calificar_criterio_entregable(
                rubrica_md,
                texto,
                criterio,
                pmax,
                niveles=niveles,
            )
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
