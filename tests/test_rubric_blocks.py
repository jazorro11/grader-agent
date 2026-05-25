from grader_agent.grading.rubric_blocks import bloque_niveles_usuario


def test_bloque_niveles_vacio():
    assert bloque_niveles_usuario(None) == ""
    assert bloque_niveles_usuario([]) == ""


def test_bloque_niveles_formatea():
    s = bloque_niveles_usuario([{"etiqueta": "A", "puntos": 0}, {"etiqueta": "B", "puntos": 4}])
    assert "NIVELES" in s
    assert "A: 0 puntos" in s
    assert "B: 4 puntos" in s
