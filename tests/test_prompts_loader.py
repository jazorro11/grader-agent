"""Tests for prompt loading (real package prompt files)."""

from grader_agent.prompts_loader import (
    system_prompt_pdf_evaluar_criterio,
    system_prompt_pdf_listar_criterios,
    system_prompt_texto_item,
)


def _assert_prompt_compuesto_incluye_evaluador_y_retro(text: str) -> None:
    low = text.lower()
    assert "evaluador" in low and "estricto" in low
    assert "retroalimentaci" in low and "retroalimentacion`" in text
    assert "colombia" in low and "sin voseo" in low
    # Frase estable de _retro_alumno.md (no está en los cuerpos texto_item/pdf solos).
    assert "Háblale con tú" in text


def test_system_prompt_texto_item_incluye_base_retro_y_cuerpo():
    text = system_prompt_texto_item()
    assert len(text) > 100
    _assert_prompt_compuesto_incluye_evaluador_y_retro(text)
    low = text.lower()
    assert "parcial (texto" in low
    assert '"pregunta"' in text
    assert '"retroalimentacion"' in text
    idx_chequeo = text.rfind("Chequeo antes de devolver el JSON")
    idx_cuerpo = low.rfind("ítem de parcial")
    assert idx_chequeo != -1 and idx_cuerpo != -1
    assert idx_chequeo > idx_cuerpo


def test_system_prompt_pdf_evaluar_incluye_base_retro_y_criterio_pdf():
    text = system_prompt_pdf_evaluar_criterio()
    assert len(text) > 100
    _assert_prompt_compuesto_incluye_evaluador_y_retro(text)
    low = text.lower()
    assert "texto del pdf" in low
    assert '"criterio"' in text
    # Retro al final del system para adherencia al tono
    idx_chequeo = text.rfind("Chequeo antes de devolver el JSON")
    idx_cuerpo = text.lower().rfind("texto del pdf")
    assert idx_chequeo != -1 and idx_cuerpo != -1
    assert idx_chequeo > idx_cuerpo


def test_system_prompt_pdf_listar_no_incluye_bloque_retro_alumno():
    text = system_prompt_pdf_listar_criterios()
    assert "Evaluador académico" not in text
    assert "Háblale con tú" not in text
    assert '"criterios"' in text
    # OpenAI exige la palabra "json" en messages con response_format json_object
    assert "json" in text.lower()
