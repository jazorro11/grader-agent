"""Tests de rutas Flask para entregables .txt y .json (sin API real)."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch

import app.routes as routes_module
from grader_agent.models import CriterionScore, GradingResult
from tests.conftest import write_rubrica_parcial


def _fake_grading_result(alumno: str = "Ana") -> GradingResult:
    return GradingResult(
        scores_by_criterion={"Criterio 1": CriterionScore(8.0, 10.0, "Bien")},
        total_score=8.0,
        total_max_score=10.0,
        feedback="Buen trabajo.",
        student_name=alumno,
        item_label=None,
        transcription=None,
        deliverable_kind="plain_text_deliverable",
        status="success",
        rejection=None,
    )


# ---------------------------------------------------------------------------
# Single-file: /calificar-entregable
# ---------------------------------------------------------------------------


@patch.object(routes_module, "run_grading_request")
def test_entregable_txt_es_aceptado(mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_run.return_value = _fake_grading_result("Luis")
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Luis",
            "entregable": (BytesIO(b"Este es mi ensayo.\n"), "entrega.txt"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["alumno"] == "Luis"
    assert body["total_obtenido"] == 8.0
    mock_run.assert_called_once()


@patch.object(routes_module, "run_grading_request")
def test_entregable_json_es_aceptado(mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_run.return_value = _fake_grading_result("Maria")
    payload = json.dumps({"respuesta": "Mi respuesta completa."}).encode("utf-8")
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Maria",
            "entregable": (BytesIO(payload), "entrega.json"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["alumno"] == "Maria"
    mock_run.assert_called_once()


def test_entregable_csv_es_rechazado(app_client):
    write_rubrica_parcial(app_client["rubrics"])
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Pedro",
            "entregable": (BytesIO(b"a,b,c\n1,2,3\n"), "datos.csv"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "error" in body


def test_entregable_sin_rubrica_devuelve_400(app_client):
    rv = app_client["client"].post(
        "/calificar-entregable",
        data={
            "alumno": "Pedro",
            "entregable": (BytesIO(b"Texto de ensayo."), "ensayo.txt"),
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 400
    body = rv.get_json()
    assert "rúbrica" in body["error"].lower()


# ---------------------------------------------------------------------------
# Batch: /calificar-carpeta-entregables
# ---------------------------------------------------------------------------


@patch.object(routes_module, "run_grading_request")
@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_txt_aparece_en_resultados(mock_meta, mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]
    mock_run.return_value = _fake_grading_result("Carlos")

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(b"Mi ensayo en texto.\n"), "entrega.txt"),
            "alumno": "Carlos",
            "nombre_completo": "Carlos López",
            "id_estudiante": "12345",
            "carpeta_origen": "",
            "archivo_entregable": "entrega.txt",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert len(body["resultados"]) == 1
    assert body["errores"] == []
    assert body["resultados"][0]["alumno"] == "Carlos"


@patch.object(routes_module, "run_grading_request")
@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_json_aparece_en_resultados(mock_meta, mock_run, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]
    mock_run.return_value = _fake_grading_result("Sofía")
    payload = json.dumps({"respuesta": "respuesta JSON"}).encode("utf-8")

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(payload), "entrega.json"),
            "alumno": "Sofía",
            "nombre_completo": "Sofía Gómez",
            "id_estudiante": "67890",
            "carpeta_origen": "",
            "archivo_entregable": "entrega.json",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert len(body["resultados"]) == 1
    assert body["errores"] == []


@patch("app.routes.metadatos_criterios_desde_rubrica")
def test_batch_extension_invalida_aparece_en_errores(mock_meta, app_client):
    write_rubrica_parcial(app_client["rubrics"])
    mock_meta.return_value = [{"criterio": "Criterio 1", "puntaje_maximo": 10.0}]

    rv = app_client["client"].post(
        "/calificar-carpeta-entregables",
        data={
            "entregable": (BytesIO(b"a,b,c"), "datos.csv"),
            "alumno": "Pedro",
            "nombre_completo": "",
            "id_estudiante": "",
            "carpeta_origen": "",
            "archivo_entregable": "datos.csv",
        },
        content_type="multipart/form-data",
    )
    assert rv.status_code == 200
    body = rv.get_json()
    assert body["resultados"] == []
    assert len(body["errores"]) == 1
    assert body["errores"][0]["alumno"] == "Pedro"
