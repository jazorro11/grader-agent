import json

import grader_agent.web.app as app_module


def test_guardar_resultado_acumula_en_json(app_client):
    """_guardar_resultado usa RESULTS_DIR aislado del fixture."""
    res_dir = app_client["results"]
    r1 = {"alumno": "A", "puntaje_obtenido": 1, "puntaje_maximo": 2}
    r2 = {"alumno": "B", "puntaje_obtenido": 3, "puntaje_maximo": 4}
    app_module._guardar_resultado("A", r1)
    app_module._guardar_resultado("B", r2)
    ruta = res_dir / "resultados.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos == [r1, r2]
