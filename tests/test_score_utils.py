from grader_agent.grading.score_utils import (
    ajustar_puntaje_a_niveles_discretos,
    clamp_puntaje,
)


def test_clamp_puntaje_rango():
    assert clamp_puntaje(5, 10) == 5.0
    assert clamp_puntaje(15, 10) == 10.0
    assert clamp_puntaje(-1, 10) == 0.0


def test_clamp_puntaje_no_numerico():
    assert clamp_puntaje("x", 10) == 0.0


def test_ajustar_a_niveles_sin_niveles_es_clamp():
    assert ajustar_puntaje_a_niveles_discretos(3.3, None, 10) == 3.3


def test_ajustar_a_niveles_elige_mas_cercano():
    niveles = [{"etiqueta": "A", "puntos": 0}, {"etiqueta": "B", "puntos": 4}]
    assert ajustar_puntaje_a_niveles_discretos(3, niveles, 10) == 4.0
    assert ajustar_puntaje_a_niveles_discretos(1, niveles, 10) == 0.0
