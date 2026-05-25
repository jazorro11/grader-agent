"""Tests para PlainTextExtractionService (sin API)."""
from __future__ import annotations

import json

import pytest

from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult
from grader_agent.services.plain_text_extraction import PlainTextExtractionService


@pytest.fixture
def svc():
    return PlainTextExtractionService()


def test_txt_happy_path(svc, tmp_path):
    p = tmp_path / "ensayo.txt"
    p.write_text("Hola mundo\nSegunda línea.\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert "Hola mundo" in out
    assert "Segunda línea" in out


def test_txt_bom_utf8_se_procesa(svc, tmp_path):
    p = tmp_path / "bom.txt"
    p.write_bytes(b"\xef\xbb\xbfContenido con BOM")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert out.startswith("Contenido con BOM")


def test_txt_vacio_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty.txt"
    p.write_text("   \n\t\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_txt_no_utf8_devuelve_error(svc, tmp_path):
    p = tmp_path / "latin.txt"
    p.write_bytes(b"\x80\x81\x82")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_txt_supera_max_bytes_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "2048")
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * 3000)
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "bytes" in out.message.lower()


def test_txt_supera_max_chars_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_CHARS", "5000")
    p = tmp_path / "long.txt"
    p.write_text("x" * 6000, encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "caracteres" in out.message.lower()


def test_json_happy_path(svc, tmp_path):
    payload = {"respuesta": "hola", "criterio": "ortografía"}
    p = tmp_path / "sub.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"respuesta"' in out
    assert '"ortografía"' in out


def test_json_lista_no_vacia(svc, tmp_path):
    p = tmp_path / "lista.json"
    p.write_text(json.dumps([{"a": 1}, {"b": 2}]), encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"a"' in out


def test_json_bom_utf8(svc, tmp_path):
    p = tmp_path / "bom.json"
    content = b"\xef\xbb\xbf" + json.dumps({"k": "v"}).encode("utf-8")
    p.write_bytes(content)
    out = svc.extract(str(p))
    assert isinstance(out, str)
    assert '"k"' in out


def test_json_invalido_devuelve_error(svc, tmp_path):
    p = tmp_path / "bad.json"
    p.write_text("{no es json", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "json" in out.message.lower()


def test_json_dict_vacio_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty_dict.json"
    p.write_text("{}", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_lista_vacia_devuelve_error(svc, tmp_path):
    p = tmp_path / "empty_list.json"
    p.write_text("[]", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_null_devuelve_error(svc, tmp_path):
    p = tmp_path / "null.json"
    p.write_text("null", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_json_supera_max_bytes_devuelve_error(svc, monkeypatch, tmp_path):
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "2048")
    p = tmp_path / "big.json"
    p.write_bytes(b'{"k":"' + b"x" * 3000 + b'"}')
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert "bytes" in out.message.lower()


def test_ruta_vacia_devuelve_error(svc):
    out = svc.extract("  ")
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_archivo_inexistente_devuelve_error(svc, tmp_path):
    out = svc.extract(str(tmp_path / "missing.txt"))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_extension_desconocida_devuelve_error(svc, tmp_path):
    p = tmp_path / "datos.csv"
    p.write_text("a,b,c\n1,2,3\n", encoding="utf-8")
    out = svc.extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION
    assert ".csv" in (out.detail or "")
