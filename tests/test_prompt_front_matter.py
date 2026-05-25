"""Tests para strip_yaml_front_matter."""

from grader_agent.prompt_front_matter import strip_yaml_front_matter


def test_strip_yaml_front_matter_quita_bloque_tipico():
    raw = """---
version: "1"
date: "2026-04-22"
changelog: "x"
---

Cuerpo del prompt.
"""
    assert strip_yaml_front_matter(raw) == "Cuerpo del prompt."


def test_sin_front_matter_devuelve_strip():
    assert strip_yaml_front_matter("  hola  ") == "hola"


def test_front_matter_incompleto_no_borra_todo():
    raw = """---
sin cierre
sigue
"""
    assert strip_yaml_front_matter(raw) == raw.strip()
