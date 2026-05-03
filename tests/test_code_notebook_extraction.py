"""Extracción de entregables .py y .ipynb (sin API)."""

from __future__ import annotations

import json

from grader_agent.models import ERROR_TYPE_VALIDATION, ErrorResult
from grader_agent.services.code_notebook_extraction import CodeNotebookExtractionService


def test_extrae_python_utf8(tmp_path) -> None:
    p = tmp_path / "a.py"
    p.write_text("# hi\nprint(42)\n", encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, str)
    assert "# hi" in out and "print(42)" in out


def test_python_vacio_devuelve_error(tmp_path) -> None:
    p = tmp_path / "empty.py"
    p.write_text("  \n\t\n", encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_python_no_utf8_devuelve_error(tmp_path) -> None:
    p = tmp_path / "bad.py"
    p.write_bytes(b"\xff\xfe\x00")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_ruta_vacia_devuelve_error() -> None:
    out = CodeNotebookExtractionService().extract("  ")
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_archivo_inexistente_devuelve_error(tmp_path) -> None:
    out = CodeNotebookExtractionService().extract(str(tmp_path / "missing.py"))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_notebook_extrae_celdas_codigo(tmp_path) -> None:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [
            {"cell_type": "markdown", "metadata": {}, "source": ["# t\n"]},
            {"cell_type": "code", "metadata": {}, "outputs": [], "source": ["x = 1\n"]},
        ],
    }
    p = tmp_path / "t.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, str)
    assert "x = 1" in out
    assert "celda código 1" in out


def test_notebook_sin_codigo_devuelve_error(tmp_path) -> None:
    nb = {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {},
        "cells": [{"cell_type": "markdown", "metadata": {}, "source": ["x"]}],
    }
    p = tmp_path / "m.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "celdas de código" in out.message.lower()


def test_notebook_nbformat_bajo_devuelve_error(tmp_path) -> None:
    nb = {"nbformat": 3, "cells": []}
    p = tmp_path / "old.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_notebook_json_invalido_devuelve_error(tmp_path) -> None:
    p = tmp_path / "broken.ipynb"
    p.write_text("{not json", encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "json" in out.message.lower()


def test_notebook_raiz_no_objeto_devuelve_error(tmp_path) -> None:
    p = tmp_path / "list_root.ipynb"
    p.write_text(json.dumps([]), encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "objeto" in out.message.lower()


def test_extension_no_permitida(tmp_path) -> None:
    p = tmp_path / "x.txt"
    p.write_text("a", encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert out.error_type == ERROR_TYPE_VALIDATION


def test_supera_max_bytes(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "2048")
    p = tmp_path / "big.py"
    p.write_bytes(b"x" * 3000)
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "bytes" in out.message.lower()


def test_supera_max_chars(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GRADER_CODE_MAX_CHARS", "5000")
    p = tmp_path / "long.py"
    p.write_text("x" * 6000, encoding="utf-8")
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "caracteres" in out.message.lower()


def test_supera_max_bytes_limite_minimo_grading_config(monkeypatch, tmp_path) -> None:
    # Límite efectivo mínimo vía grading_config es 1024 bytes
    monkeypatch.setenv("GRADER_CODE_MAX_BYTES", "1024")
    p = tmp_path / "huge.py"
    p.write_bytes(b"x" * 2000)
    out = CodeNotebookExtractionService().extract(str(p))
    assert isinstance(out, ErrorResult)
    assert "bytes" in out.message.lower()
