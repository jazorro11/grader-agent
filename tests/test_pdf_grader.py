from unittest.mock import MagicMock, patch

import pytest

import grader_agent.grading.pdf as pdf_grader


def _assert_openrouter_client_first_arg(mock_json: MagicMock) -> None:
    for call in mock_json.call_args_list:
        assert call.args[0] is pdf_grader.client


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_listar_criterios_desde_rubrica_extrae_nombres(mock_json: MagicMock) -> None:
    fake_json = (
        '{"criterios": ['
        '{"criterio": "Criterio A", "puntaje_maximo": 5},'
        '{"criterio": "Criterio B", "puntaje_maximo": 3}'
        "]}"
    )
    mock_json.return_value = fake_json

    out = pdf_grader.listar_criterios_desde_rubrica("# rubrica")

    assert out == ["Criterio A", "Criterio B"]
    mock_json.assert_called_once()
    _assert_openrouter_client_first_arg(mock_json)


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_metadatos_criterios_desde_rubrica_parsea_niveles(mock_json: MagicMock) -> None:
    fake_json = (
        '{"criterios": ['
        '{"criterio": "Uno", "puntaje_maximo": 4, '
        '"niveles": [{"etiqueta": "Bajo", "puntos": 0}, {"etiqueta": "Alto", "puntos": 4}]}'
        "]}"
    )
    mock_json.return_value = fake_json

    meta = pdf_grader.metadatos_criterios_desde_rubrica("# r")

    assert len(meta) == 1
    assert meta[0]["criterio"] == "Uno"
    assert meta[0]["puntaje_maximo"] == 4.0
    assert len(meta[0]["niveles"]) == 2


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_metadatos_criterios_json_invalido_devuelve_vacio(mock_json: MagicMock) -> None:
    mock_json.return_value = "no es json"
    assert pdf_grader.metadatos_criterios_desde_rubrica("x") == []


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_metadatos_criterios_criterios_no_lista_devuelve_vacio(mock_json: MagicMock) -> None:
    mock_json.return_value = '{"criterios": "mal formado"}'
    assert pdf_grader.metadatos_criterios_desde_rubrica("# r") == []


@patch.object(pdf_grader, "calificar_criterio_entregable")
@patch.object(pdf_grader, "metadatos_criterios_desde_rubrica")
def test_calificar_entregable_pdf_suma_criterios(mock_meta, mock_cal_criterio):
    mock_meta.return_value = [
        {"criterio": "Uno", "puntaje_maximo": 5},
        {"criterio": "Dos", "puntaje_maximo": 5},
    ]
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

    resultado = pdf_grader.calificar_entregable_pdf("# r", "texto del alumno", "Ana")

    assert resultado["tipo"] == "entregable"
    assert resultado["alumno"] == "Ana"
    assert resultado["total_obtenido"] == 7
    assert resultado["total_maximo"] == 10
    assert len(resultado["criterios"]) == 2
    mock_meta.assert_called_once_with("# r")


@patch.object(pdf_grader, "calificar_criterio_entregable")
@patch.object(pdf_grader, "metadatos_criterios_desde_rubrica")
def test_calificar_entregable_pdf_criterios_precalculados_filtra_metadatos(
    mock_meta, mock_cal_criterio
):
    mock_meta.return_value = [
        {"criterio": "Pre", "puntaje_maximo": 10},
        {"criterio": "Otro", "puntaje_maximo": 5},
    ]
    mock_cal_criterio.return_value = {
        "criterio": "Pre",
        "puntaje_obtenido": 10,
        "puntaje_maximo": 10,
        "retroalimentacion": "ok",
    }

    resultado = pdf_grader.calificar_entregable_pdf(
        "# r", "texto del alumno", "Leo", criterios=["Pre"]
    )

    mock_meta.assert_called_once_with("# r")
    mock_cal_criterio.assert_called_once()
    assert mock_cal_criterio.call_args[0][2] == "Pre"
    assert mock_cal_criterio.call_args[0][3] == 10
    assert resultado["total_obtenido"] == 10
    assert len(resultado["criterios"]) == 1


@patch.object(pdf_grader, "calificar_criterio_entregable")
@patch.object(pdf_grader, "metadatos_criterios_desde_rubrica")
def test_calificar_entregable_pdf_metadatos_precargados_evita_reparse(
    mock_meta, mock_cal
):
    mock_cal.return_value = {
        "criterio": "A",
        "puntaje_obtenido": 1,
        "puntaje_maximo": 2,
        "retroalimentacion": "x",
    }
    meta = [{"criterio": "A", "puntaje_maximo": 2}]

    pdf_grader.calificar_entregable_pdf(
        "# r", "texto del alumno", "N", metadatos_criterios=meta
    )

    mock_meta.assert_not_called()
    mock_cal.assert_called_once()


@patch.object(pdf_grader, "metadatos_criterios_desde_rubrica", return_value=[])
def test_calificar_entregable_pdf_sin_criterios_valueerror(mock_list):
    with pytest.raises(ValueError, match="criterios evaluables"):
        pdf_grader.calificar_entregable_pdf("# r", "texto", "X")


@patch.object(pdf_grader, "metadatos_criterios_desde_rubrica")
def test_calificar_entregable_pdf_lista_criterios_vacia_valueerror(mock_meta):
    with pytest.raises(ValueError, match="criterios evaluables"):
        pdf_grader.calificar_entregable_pdf(
            "# r",
            "texto",
            "X",
            criterios=[],
            metadatos_criterios=[{"criterio": "X", "puntaje_maximo": 1}],
        )
    mock_meta.assert_not_called()


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_calificar_criterio_entregable_usa_maximo_canonico(mock_json: MagicMock, tmp_path):
    mock_json.side_effect = [
        '{"puntaje_obtenido": 999}',
        '{"retroalimentacion": "ok"}',
    ]

    out = pdf_grader.calificar_criterio_entregable("# r", "texto", "C1", 4.0)

    assert out["puntaje_maximo"] == 4.0
    assert out["puntaje_obtenido"] == 4.0
    assert out["retroalimentacion"] == "ok"
    assert mock_json.call_count == 2
    _assert_openrouter_client_first_arg(mock_json)


@patch("grader_agent.grading.pdf.chat_completion_json_content")
def test_calificar_criterio_entregable_respeta_niveles_discretos(mock_json: MagicMock):
    niveles = [
        {"etiqueta": "Bajo", "puntos": 0},
        {"etiqueta": "Alto", "puntos": 5},
    ]
    mock_json.side_effect = [
        '{"puntaje_obtenido": 2}',
        '{"retroalimentacion": "r"}',
    ]

    out = pdf_grader.calificar_criterio_entregable("# r", "texto", "C1", 5.0, niveles=niveles)

    assert out["puntaje_obtenido"] == 0.0
    assert out["puntaje_maximo"] == 5.0


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


def test_extraer_texto_pdf_rechaza_mas_de_cuatro_paginas(monkeypatch):
    monkeypatch.setenv("GRADER_PDF_MAX_PAGES", "4")
    largo = _FakeDocLargo()
    with patch("grader_agent.services.pdf_extraction.fitz.open", return_value=largo):
        with pytest.raises(ValueError, match="5 páginas"):
            pdf_grader.extraer_texto_pdf("cualquier.pdf")
    assert largo.closed


def test_extraer_texto_pdf_acepta_mas_paginas_si_limite_env_alto(monkeypatch):
    monkeypatch.setenv("GRADER_PDF_MAX_PAGES", "10")

    class _FakePage:
        def get_text(self):
            return "x"

    class _FakeDocSeis:
        def __len__(self):
            return 6

        def __iter__(self):
            return iter([_FakePage() for _ in range(6)])

        def close(self):
            pass

    doc = _FakeDocSeis()
    with patch("grader_agent.services.pdf_extraction.fitz.open", return_value=doc):
        texto = pdf_grader.extraer_texto_pdf("informe.pdf")
    assert texto == "\n".join(["x"] * 6)


def test_extraer_texto_pdf_concatena_texto_hasta_cuatro_paginas():
    doc = _FakeDocCorto()
    with patch("grader_agent.services.pdf_extraction.fitz.open", return_value=doc):
        texto = pdf_grader.extraer_texto_pdf("informe.pdf")
    assert texto == "contenido"
