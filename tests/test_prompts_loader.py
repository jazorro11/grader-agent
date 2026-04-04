"""Tests for prompt loading (real package prompt files)."""

from grader_agent.prompts_loader import system_prompt_texto_item


def test_system_prompt_texto_item_incluye_base_y_cuerpo_especifico():
    text = system_prompt_texto_item()
    assert len(text) > 100
    assert "evaluador académico" in text
    assert "ítem de parcial" in text
