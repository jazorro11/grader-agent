"""Tests for prompt loading (real package prompt files)."""

from grader_agent.prompts_loader import (
    system_prompt_pdf_listar_criterios,
    system_prompt_pdf_puntaje_criterio,
    system_prompt_pdf_retro_criterio,
    system_prompt_texto_escala_item,
    system_prompt_texto_puntaje_item,
    system_prompt_texto_retro_item,
)


def _assert_prompt_incluye_base_evaluador(text: str) -> None:
    low = text.lower()
    assert "evaluador" in low and "estricto" in low
    assert "colombia" in low and "sin voseo" in low


def test_system_prompt_pdf_puntaje_incluye_base_sin_bloque_retro_completo():
    text = system_prompt_pdf_puntaje_criterio()
    assert len(text) > 100
    _assert_prompt_incluye_base_evaluador(text)
    assert '"puntaje_obtenido"' in text
    assert "puntaje máximo canónico" in text.lower()
    assert "Háblale con tú" not in text


def test_system_prompt_pdf_retro_incluye_retro_alumno():
    text = system_prompt_pdf_retro_criterio()
    assert len(text) > 100
    assert "Háblale con tú" in text
    assert "Chequeo antes de devolver el JSON" in text
    assert '"retroalimentacion"' in text


def test_system_prompt_pdf_listar_no_incluye_bloque_retro_alumno():
    text = system_prompt_pdf_listar_criterios()
    assert "Evaluador académico" not in text
    assert "Háblale con tú" not in text
    assert '"criterios"' in text
    assert "puntaje_maximo" in text
    assert "json" in text.lower()


def test_system_prompt_texto_escala_es_ligero():
    text = system_prompt_texto_escala_item()
    assert "puntaje_maximo" in text
    assert "Evaluador académico" not in text


def test_system_prompt_texto_puntaje_incluye_base():
    text = system_prompt_texto_puntaje_item()
    _assert_prompt_incluye_base_evaluador(text)
    assert '"puntaje_obtenido"' in text


def test_system_prompt_texto_retro_incluye_retro_alumno():
    text = system_prompt_texto_retro_item()
    assert "Háblale con tú" in text
    assert '"retroalimentacion"' in text
