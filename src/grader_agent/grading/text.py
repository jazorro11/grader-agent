"""Text-item grading: rubric scale, score, and short feedback via chat completions."""

from __future__ import annotations

from grader_agent.grading.llm_json import json_object_from_message_content
from grader_agent.grading.rubric_blocks import bloque_niveles_usuario
from grader_agent.grading.score_utils import ajustar_puntaje_a_niveles_discretos
from grader_agent.grading_config import retro_temperature, score_temperature
from grader_agent.llm.client_calls import chat_completion_json_content
from grader_agent.llm.clients import get_default_openrouter_chat_client
from grader_agent.settings import chat_model
from grader_agent.prompts_loader import (
    system_prompt_texto_escala_item,
    system_prompt_texto_puntaje_item,
    system_prompt_texto_retro_item,
)

client = get_default_openrouter_chat_client()


def escala_item_desde_rubrica(rubrica_md: str, pregunta: str) -> dict:
    """
    Locate the rubric item and return canonical max score and optional discrete levels.
    """
    user_message = f"""RÚBRICA:
{rubrica_md}

ÍTEM (docente): {pregunta}
"""
    raw = chat_completion_json_content(
        client,
        model=chat_model(),
        system=system_prompt_texto_escala_item(),
        user=user_message,
        temperature=0,
        kind="escala",
    )
    data = json_object_from_message_content(raw)
    if not data:
        raise ValueError(
            "No se pudo interpretar la escala del ítem en la rúbrica. "
            "Revisá la pregunta y el archivo .md."
        )
    try:
        max_pts = float(data.get("puntaje_maximo", 0))
    except (TypeError, ValueError):
        max_pts = 0.0
    if max_pts <= 0:
        raise ValueError(
            "No se ubicó el ítem en la rúbrica o no tiene puntaje. "
            "Revisá la pregunta y que la rúbrica describa ese ítem con puntaje."
        )
    item_raw = data.get("item")
    item = str(item_raw).strip() if item_raw is not None else ""
    if not item:
        item = pregunta.strip()
    niveles = data.get("niveles")
    cleaned = None
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
        if not cleaned:
            cleaned = None
    return {"item": item, "puntaje_maximo": max_pts, "niveles": cleaned}


def calificar_respuesta(rubrica_md: str, pregunta: str, respuesta_alumno: str) -> dict:
    """Grade one free-text answer against a markdown rubric (score + feedback JSON)."""
    escala = escala_item_desde_rubrica(rubrica_md, pregunta)
    item_label = escala["item"]
    puntaje_maximo = escala["puntaje_maximo"]
    niveles = escala.get("niveles")

    bloque_n = bloque_niveles_usuario(niveles)
    user_puntaje = f"""RÚBRICA:
{rubrica_md}

ÍTEM: {pregunta}
MÁX canónico (techo; no reinterpretes; el sistema fija el máximo en salida): {puntaje_maximo}
{bloque_n}RESPUESTA: {respuesta_alumno}
"""

    raw_p = chat_completion_json_content(
        client,
        model=chat_model(),
        system=system_prompt_texto_puntaje_item(),
        user=user_puntaje,
        temperature=score_temperature(),
        kind="puntaje",
    )
    data_p = json_object_from_message_content(raw_p)
    try:
        bruto = float(data_p.get("puntaje_obtenido", 0))
    except (TypeError, ValueError):
        bruto = 0.0
    puntaje_obtenido = ajustar_puntaje_a_niveles_discretos(bruto, niveles, puntaje_maximo)

    user_retro = f"""RÚBRICA:
{rubrica_md}

ÍTEM: {pregunta}
PUNTAJE fijo: {puntaje_obtenido}/{puntaje_maximo}

RESPUESTA: {respuesta_alumno}
"""

    raw_r = chat_completion_json_content(
        client,
        model=chat_model(),
        system=system_prompt_texto_retro_item(),
        user=user_retro,
        temperature=retro_temperature(),
        kind="retro",
    )
    data_r = json_object_from_message_content(raw_r)
    retro = data_r.get("retroalimentacion")
    if not isinstance(retro, str):
        retro = ""
    pregunta_out = data_r.get("pregunta")
    if isinstance(pregunta_out, str) and pregunta_out.strip():
        etiqueta_pregunta = pregunta_out.strip()
    else:
        etiqueta_pregunta = item_label

    return {
        "pregunta": etiqueta_pregunta,
        "puntaje_obtenido": puntaje_obtenido,
        "puntaje_maximo": puntaje_maximo,
        "retroalimentacion": retro,
    }
