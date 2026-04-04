from unittest.mock import MagicMock, patch

import pytest

import pdf_grader


def test_listar_criterios_desde_rubrica_parsea_json():
    fake_json = '{"criterios": ["Criterio A", "Criterio B"]}'
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content=fake_json))]
    mock_create = MagicMock(return_value=mock_resp)

    with patch.object(pdf_grader.client.chat.completions, "create", mock_create):
        out = pdf_grader.listar_criterios_desde_rubrica("# rubrica")

    assert out == ["Criterio A", "Criterio B"]
    mock_create.assert_called_once()


def test_listar_criterios_desde_rubrica_json_invalido_devuelve_vacio():
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="no es json"))]

    with patch.object(pdf_grader.client.chat.completions, "create", return_value=mock_resp):
        assert pdf_grader.listar_criterios_desde_rubrica("x") == []


def test_listar_criterios_desde_rubrica_criterios_no_lista_devuelve_vacio():
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(message=MagicMock(content='{"criterios": "mal formado"}'))
    ]
    with patch.object(pdf_grader.client.chat.completions, "create", return_value=mock_resp):
        assert pdf_grader.listar_criterios_desde_rubrica("# r") == []


@patch.object(pdf_grader, "calificar_criterio_entregable")
@patch.object(pdf_grader, "listar_criterios_desde_rubrica")
@patch.object(pdf_grader, "extraer_texto_pdf")
def test_calificar_entregable_pdf_suma_criterios(
    mock_extraer, mock_listar, mock_cal_criterio, tmp_path
):
    mock_extraer.return_value = "texto pdf"
    mock_listar.return_value = ["Uno", "Dos"]
    mock_cal_criterio.side_effect = [
        {
            "criterio": "Uno",
            "puntaje_obtenido": 4,
            "puntaje_maximo": 5,
            "retroalimentacion": "r1",
        },
        {
            "criterio": "Dos",
            "puntaje_obtenido": 3,
            "puntaje_maximo": 5,
            "retroalimentacion": "r2",
        },
    ]

    pdf_path = tmp_path / "t.pdf"
    pdf_path.write_bytes(b"x")

    resultado = pdf_grader.calificar_entregable_pdf("# r", str(pdf_path), "Ana")

    assert resultado["tipo"] == "entregable_pdf"
    assert resultado["alumno"] == "Ana"
    assert resultado["total_obtenido"] == 7
    assert resultado["total_maximo"] == 10
    assert len(resultado["criterios"]) == 2
    assert not pdf_path.exists()


@patch.object(pdf_grader, "listar_criterios_desde_rubrica", return_value=[])
@patch.object(pdf_grader, "extraer_texto_pdf", return_value="t")
def test_calificar_entregable_pdf_sin_criterios_valueerror(mock_ext, mock_list, tmp_path):
    pdf_path = tmp_path / "t.pdf"
    pdf_path.write_bytes(b"x")
    with pytest.raises(ValueError, match="criterios evaluables"):
        pdf_grader.calificar_entregable_pdf("# r", str(pdf_path), "X")


class _FakePage:
    def get_text(self):
        return "contenido "


class _FakeDocCorto:
    def __init__(self):
        self._pages = [_FakePage()]

    def __len__(self):
        return len(self._pages)

    def __iter__(self):
        return iter(self._pages)

    def close(self):
        pass


class _FakeDocLargo:
    def __init__(self):
        self.closed = False

    def __len__(self):
        return 5

    def close(self):
        self.closed = True


def test_extraer_texto_pdf_rechaza_mas_de_cuatro_paginas():
    largo = _FakeDocLargo()
    with patch("pdf_grader.fitz.open", return_value=largo):
        with pytest.raises(ValueError, match="5 páginas"):
            pdf_grader.extraer_texto_pdf("cualquier.pdf")
    assert largo.closed


def test_extraer_texto_pdf_concatena_texto_hasta_cuatro_paginas():
    doc = _FakeDocCorto()
    with patch("pdf_grader.fitz.open", return_value=doc):
        texto = pdf_grader.extraer_texto_pdf("informe.pdf")
    assert texto == "contenido"
