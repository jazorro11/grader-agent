import json
import pytest
import grader_agent.grading.pdf as pdf_grader


def test_extraer_texto_json_dict_valido(tmp_path):
    f = tmp_path / "entrega.json"
    f.write_text(json.dumps({"respuesta": "texto del alumno", "seccion": "A"}), encoding="utf-8")
    resultado = pdf_grader.extraer_texto_json(str(f))
    assert isinstance(resultado, str)
    assert "texto del alumno" in resultado


def test_extraer_texto_json_array_valido(tmp_path):
    f = tmp_path / "entrega.json"
    f.write_text(json.dumps([{"p": "P1", "r": "respuesta uno"}]), encoding="utf-8")
    resultado = pdf_grader.extraer_texto_json(str(f))
    assert isinstance(resultado, str)
    assert "respuesta uno" in resultado


def test_extraer_texto_json_no_json_lanza_valueerror(tmp_path):
    f = tmp_path / "mal.json"
    f.write_bytes(b"esto no es json {{{")
    with pytest.raises(ValueError, match="JSON"):
        pdf_grader.extraer_texto_json(str(f))


def test_extraer_texto_json_objeto_vacio_lanza_valueerror(tmp_path):
    f = tmp_path / "vacio.json"
    f.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="contenido evaluable"):
        pdf_grader.extraer_texto_json(str(f))
