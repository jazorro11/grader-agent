import json
from io import BytesIO
from unittest.mock import patch

import pytest

import grader_agent.web.app as app_module
from tests.conftest import write_rubrica_parcial


def test_index_devuelve_200(app_client):
    rv = app_client["client"].get("/")
    assert rv.status_code == 200
    assert b"html" in rv.data.lower()


def test_calificar_texto_sin_rubrica_devuelve_400(app_client):
    c = app_client["client"]
    rv = c.post(
        "/calificar-texto",
        json={"pregunta": "P1", "respuesta": "R", "alumno": "Ana"},
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body
    assert "rúbrica" in body["error"].lower()


def test_calificar_texto_json_invalido_devuelve_400(app_client):
    c = app_client["client"]
    rv = c.post(
        "/calificar-texto",
        data="{no es json",
        content_type="application/json",
    )
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "Se esperaba un cuerpo JSON válido"


def test_calificar_texto_sin_content_type_json_devuelve_400(app_client):
    c = app_client["client"]
    rv = c.post("/calificar-texto", data="algo")
    assert rv.status_code == 400
    assert "JSON" in rv.get_json()["error"]


@patch.object(app_module, "calificar_respuesta")
def test_calificar_texto_camino_feliz_guarda_resultado(
    mock_calificar, app_client
):
    write_rubrica_parcial(app_client["rubrics"])
    mock_calificar.return_value = {
        "pregunta": "P1",
        "puntaje_obtenido": 7,
        "puntaje_maximo": 10,
        "retroalimentacion": "Bien",
    }
    c = app_client["client"]
    rv = c.post(
        "/calificar-texto",
        json={
            "pregunta": "P1",
            "respuesta": "texto",
            "alumno": "Luis",
        },
    )
    assert rv.status_code == 200
    data = rv.get_json()
    assert data["alumno"] == "Luis"
    assert data["puntaje_obtenido"] == 7
    mock_calificar.assert_called_once()

    ruta = app_client["results"] / "resultados.json"
    assert ruta.is_file()

    guardados = json.loads(ruta.read_text(encoding="utf-8"))
    assert len(guardados) == 1
    assert guardados[0]["alumno"] == "Luis"


def test_calificar_audio_sin_archivo_devuelve_400(app_client):
    c = app_client["client"]
    rv = c.post(
        "/calificar-audio",
        data={"pregunta": "P1", "alumno": "Ana"},
    )
    assert rv.status_code == 400
    assert "audio" in rv.get_json()["error"].lower()


@patch.object(app_module, "transcribir_audio")
def test_calificar_audio_sin_rubrica_devuelve_400(mock_tr, app_client):
    mock_tr.return_value = "transcripción simulada"
    c = app_client["client"]
    audio = (BytesIO(b"fake"), "grabacion.webm")
    rv = c.post(
        "/calificar-audio",
        data={"pregunta": "P1", "alumno": "Ana", "audio": audio},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    mock_tr.assert_called_once()


@patch.object(app_module, "calificar_respuesta")
@patch.object(app_module, "transcribir_audio")
def test_calificar_audio_camino_feliz(mock_tr, mock_cal, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_tr.return_value = "lo que dijo el alumno"
    mock_cal.return_value = {
        "pregunta": "P1",
        "puntaje_obtenido": 5,
        "puntaje_maximo": 10,
        "retroalimentacion": "Ok",
    }
    c = app_client["client"]
    rv = c.post(
        "/calificar-audio",
        data={
            "pregunta": "P1",
            "alumno": "Pepe",
            "audio": (BytesIO(b"x"), "a.webm"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["transcripcion"] == "lo que dijo el alumno"
    assert body["alumno"] == "Pepe"


def test_cargar_rubrica_sin_archivo_devuelve_400(app_client):
    rv = app_client["client"].post("/cargar-rubrica", data={})
    assert rv.status_code == 400


def test_cargar_rubrica_camino_feliz(app_client):
    rub = app_client["rubrics"]
    rv = app_client["client"].post(
        "/cargar-rubrica",
        data={"rubrica": (BytesIO(b"# Mi rubrica\n"), "r.md")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    assert (rub / "rubrica_activa.md").read_text(encoding="utf-8") == "# Mi rubrica\n"


def test_cargar_rubrica_no_utf8_devuelve_400(app_client):
    rv = app_client["client"].post(
        "/cargar-rubrica",
        data={"rubrica": (BytesIO(b"\xff\xfe\x28"), "x.md")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    assert "utf-8" in rv.get_json()["error"].lower()


def test_subida_supera_max_content_length_devuelve_413(app_client, monkeypatch):
    monkeypatch.setitem(app_module.app.config, "MAX_CONTENT_LENGTH", 80)
    rv = app_client["client"].post(
        "/cargar-rubrica",
        data={"rubrica": (BytesIO(b"#" * 200), "grande.md")},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 413
    body = rv.get_json()
    assert "error" in body
    assert "16 MB" in body["error"] or "máximo" in body["error"].lower()


def test_calificar_entregable_sin_pdf_devuelve_400(app_client):
    write_rubrica_parcial(app_client["rubrics"])
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={"alumno": "X"},
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400


def test_calificar_entregable_sin_rubrica_devuelve_400(app_client):
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "X",
            "pdf": (BytesIO(b"%PDF-1.4"), "informe.pdf"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    assert "rúbrica" in rv.get_json()["error"].lower()


@patch.object(app_module, "calificar_entregable_pdf")
def test_calificar_entregable_camino_feliz(mock_pdf, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_pdf.return_value = {
        "alumno": "María",
        "tipo": "entregable_pdf",
        "criterios": [],
        "total_obtenido": 10,
        "total_maximo": 10,
    }
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "María",
            "pdf": (BytesIO(b"%PDF-1.4 fake"), "informe.pdf"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    mock_pdf.assert_called_once()
    args, _kwargs = mock_pdf.call_args
    assert args[0]  # rubrica no vacía
    assert args[2] == "María"


@patch.object(app_module, "calificar_entregable_pdf")
def test_calificar_entregable_valueerror_devuelve_400(mock_pdf, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_pdf.side_effect = ValueError("PDF demasiado largo")
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Z",
            "pdf": (BytesIO(b"%PDF"), "i.pdf"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    assert rv.get_json()["error"] == "PDF demasiado largo"


def test_resultados_vacio_si_no_hay_archivo(app_client):
    rv = app_client["client"].get("/resultados")
    assert rv.status_code == 200
    assert rv.get_json() == []


def test_resultados_devuelve_lista_guardada(app_client):
    write_rubrica_parcial(app_client["rubrics"])
    with patch.object(app_module, "calificar_respuesta") as mock_cal:
        mock_cal.return_value = {
            "pregunta": "P",
            "puntaje_obtenido": 1,
            "puntaje_maximo": 2,
            "retroalimentacion": "x",
        }
        app_client["client"].post(
            "/calificar-texto",
            json={"pregunta": "P", "respuesta": "r", "alumno": "A"},
        )
    rv = app_client["client"].get("/resultados")
    assert rv.status_code == 200
    assert len(rv.get_json()) == 1


def test_limpiar_resultados_borra_json(app_client):
    res = app_client["results"]
    ruta = res / "resultados.json"
    ruta.write_text("[{}]", encoding="utf-8")
    rv = app_client["client"].post("/limpiar-resultados")
    assert rv.status_code == 200
    assert not ruta.exists()
