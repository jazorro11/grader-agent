from unittest.mock import MagicMock, patch

import pytest

import grader_agent.grading.text as text_grader


@patch.object(text_grader, "get_openai_client")
def test_calificar_respuesta_fija_maximo_canonico(mock_get_client):
    r_escala = MagicMock()
    r_escala.choices = [
        MagicMock(
            message=MagicMock(
                content='{"item": "P1", "puntaje_maximo": 10, "niveles": []}'
            )
        )
    ]
    r_p = MagicMock()
    r_p.choices = [MagicMock(message=MagicMock(content='{"puntaje_obtenido": 500}'))]
    r_r = MagicMock()
    r_r.choices = [
        MagicMock(
            message=MagicMock(
                content='{"pregunta": "P1", "retroalimentacion": "bien hecho"}'
            )
        )
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [r_escala, r_p, r_r]
    mock_get_client.return_value = mock_client

    out = text_grader.calificar_respuesta("# rub", "P1", "respuesta")

    assert out["puntaje_maximo"] == 10.0
    assert out["puntaje_obtenido"] == 10.0
    assert out["retroalimentacion"] == "bien hecho"
    assert mock_client.chat.completions.create.call_count == 3


@patch.object(text_grader, "get_openai_client")
def test_escala_item_json_invalido_valueerror(mock_get_client):
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="no es json"))]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp
    mock_get_client.return_value = mock_client

    with pytest.raises(ValueError, match="interpretar"):
        text_grader.escala_item_desde_rubrica("# r", "P1")


@patch.object(text_grader, "get_openai_client")
def test_escala_item_sin_puntaje_positivo_valueerror(mock_get_client):
    mock_resp = MagicMock()
    mock_resp.choices = [
        MagicMock(
            message=MagicMock(content='{"item": "P1", "puntaje_maximo": 0}')
        )
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_resp
    mock_get_client.return_value = mock_client

    with pytest.raises(ValueError, match="puntaje"):
        text_grader.escala_item_desde_rubrica("# r", "P1")


@patch.object(text_grader, "get_openai_client")
def test_calificar_respuesta_ajusta_a_niveles_discretos(mock_get_client):
    r_escala = MagicMock()
    r_escala.choices = [
        MagicMock(
            message=MagicMock(
                content=(
                    '{"item": "P1", "puntaje_maximo": 4, '
                    '"niveles": ['
                    '{"etiqueta": "Bajo", "puntos": 0}, '
                    '{"etiqueta": "Alto", "puntos": 4}'
                    "]}"
                )
            )
        )
    ]
    r_p = MagicMock()
    r_p.choices = [MagicMock(message=MagicMock(content='{"puntaje_obtenido": 3.1}'))]
    r_r = MagicMock()
    r_r.choices = [
        MagicMock(message=MagicMock(content='{"retroalimentacion": "ok"}'))
    ]
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [r_escala, r_p, r_r]
    mock_get_client.return_value = mock_client

    out = text_grader.calificar_respuesta("# r", "P1", "respuesta")

    assert out["puntaje_obtenido"] == 4.0
    assert out["puntaje_maximo"] == 4.0
