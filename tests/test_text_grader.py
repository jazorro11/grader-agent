from unittest.mock import MagicMock, patch

import pytest

import grader_agent.grading.text as text_grader


def _assert_openrouter_client_first_arg(mock_json: MagicMock) -> None:
    for call in mock_json.call_args_list:
        assert (
            call.args[0] is text_grader.client
        ), "Las llamadas de calificación deben usar el cliente OpenRouter inyectado en el módulo."


@patch("grader_agent.grading.text.chat_completion_json_content")
def test_calificar_respuesta_fija_maximo_canonico(mock_json: MagicMock) -> None:
    mock_json.side_effect = [
        '{"item": "P1", "puntaje_maximo": 10, "niveles": []}',
        '{"puntaje_obtenido": 500}',
        '{"pregunta": "P1", "retroalimentacion": "bien hecho"}',
    ]

    out = text_grader.calificar_respuesta("# rub", "P1", "respuesta")

    assert out["puntaje_maximo"] == 10.0
    assert out["puntaje_obtenido"] == 10.0
    assert out["retroalimentacion"] == "bien hecho"
    assert mock_json.call_count == 3
    _assert_openrouter_client_first_arg(mock_json)


@patch("grader_agent.grading.text.chat_completion_json_content")
def test_escala_item_json_invalido_valueerror(mock_json: MagicMock) -> None:
    mock_json.return_value = "no es json"
    with pytest.raises(ValueError, match="interpretar"):
        text_grader.escala_item_desde_rubrica("# r", "P1")
    assert mock_json.call_args.args[0] is text_grader.client


@patch("grader_agent.grading.text.chat_completion_json_content")
def test_escala_item_sin_puntaje_positivo_valueerror(mock_json: MagicMock) -> None:
    mock_json.return_value = '{"item": "P1", "puntaje_maximo": 0}'
    with pytest.raises(ValueError, match="puntaje"):
        text_grader.escala_item_desde_rubrica("# r", "P1")


@patch("grader_agent.grading.text.chat_completion_json_content")
def test_calificar_respuesta_ajusta_a_niveles_discretos(mock_json: MagicMock) -> None:
    mock_json.side_effect = [
        (
            '{"item": "P1", "puntaje_maximo": 4, '
            '"niveles": ['
            '{"etiqueta": "Bajo", "puntos": 0}, '
            '{"etiqueta": "Alto", "puntos": 4}'
            "]}"
        ),
        '{"puntaje_obtenido": 3.1}',
        '{"retroalimentacion": "ok"}',
    ]

    out = text_grader.calificar_respuesta("# r", "P1", "respuesta")

    assert out["puntaje_obtenido"] == 4.0
    assert out["puntaje_maximo"] == 4.0
    _assert_openrouter_client_first_arg(mock_json)
