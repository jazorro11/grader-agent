import json

from app.routes import _guardar_resultado


def test_guardar_resultado_acumula_en_json(app_client):
    """_guardar_resultado writes under the isolated GRADER_DATA_DIR fixture."""
    res_dir = app_client["results"]
    flask_app = app_client["app"]
    r1 = {"alumno": "A", "puntaje_obtenido": 1, "puntaje_maximo": 2}
    r2 = {"alumno": "B", "puntaje_obtenido": 3, "puntaje_maximo": 4}
    with flask_app.app_context():
        _guardar_resultado("A", r1)
        _guardar_resultado("B", r2)
    ruta = res_dir / "resultados.json"
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    assert datos == [r1, r2]
