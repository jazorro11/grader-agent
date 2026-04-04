import logging
import re

import pytest

from http_logging import configure_logging


def test_request_log_incluye_metodo_path_y_status(app_client, caplog):
    caplog.set_level(logging.INFO, logger="grader_agent.http")
    client = app_client["client"]
    rv = client.get("/")
    assert rv.status_code == 200
    mensajes = [r.message for r in caplog.records if r.name == "grader_agent.http"]
    assert mensajes
    assert "GET / -> 200" in mensajes[0]
    assert re.search(r"\(\d+\.\d+ ms\)", mensajes[0])


def test_404_log_incluye_rutas_post_y_query_bytes(app_client, caplog):
    caplog.set_level(logging.WARNING, logger="grader_agent.errors")
    client = app_client["client"]
    rv = client.post("/ruta-inventada")
    assert rv.status_code == 404
    warnings = [r.message for r in caplog.records if r.name == "grader_agent.errors"]
    assert warnings
    assert "404 POST /ruta-inventada" in warnings[0]
    assert "query_bytes=0" in warnings[0]
    assert "/calificar-entregable" in warnings[0]


def test_configure_logging_acepta_log_level_invalido_sin_crash(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "NO_EXISTE_ESTE_NIVEL")
    configure_logging()
    assert logging.getLogger().level == logging.INFO


def test_configure_logging_log_level_solo_espacios_cae_a_info(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "   ")
    configure_logging()
    assert logging.getLogger().level == logging.INFO
