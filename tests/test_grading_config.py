"""grading_config: temperaturas y límites max_completion_tokens vía monkeypatch (sin .env real)."""

import pytest

from grader_agent import grading_config


def test_score_temperature_default(monkeypatch):
    monkeypatch.delenv("GRADER_SCORE_TEMPERATURE", raising=False)
    assert grading_config.score_temperature() == 0.0


def test_retro_temperature_default(monkeypatch):
    monkeypatch.delenv("GRADER_RETRO_TEMPERATURE", raising=False)
    assert grading_config.retro_temperature() == 0.8


def test_temperatures_desde_env(monkeypatch):
    monkeypatch.setenv("GRADER_SCORE_TEMPERATURE", "0.2")
    monkeypatch.setenv("GRADER_RETRO_TEMPERATURE", "0.5")
    assert grading_config.score_temperature() == 0.2
    assert grading_config.retro_temperature() == 0.5


def test_temperatures_string_vacio_usa_default(monkeypatch):
    monkeypatch.setenv("GRADER_SCORE_TEMPERATURE", "  ")
    monkeypatch.setenv("GRADER_RETRO_TEMPERATURE", "")
    assert grading_config.score_temperature() == 0.0
    assert grading_config.retro_temperature() == 0.8


def test_temperatures_env_no_numerico_usa_default(monkeypatch):
    monkeypatch.setenv("GRADER_SCORE_TEMPERATURE", "no-float")
    monkeypatch.setenv("GRADER_RETRO_TEMPERATURE", "x")
    assert grading_config.score_temperature() == 0.0
    assert grading_config.retro_temperature() == 0.8


def test_chat_completion_limit_kwargs_defaults(monkeypatch):
    for name in (
        "GRADER_MAX_COMPLETION_ESCALA",
        "GRADER_MAX_COMPLETION_PUNTAJE",
        "GRADER_MAX_COMPLETION_LISTAR",
        "GRADER_MAX_COMPLETION_RETRO",
        "GRADER_MAX_COMPLETION_GRADING_JSON",
        "VALIDATION_MAX_TOKENS",
    ):
        monkeypatch.delenv(name, raising=False)
    expected_tokens = {
        "escala": 256,
        "puntaje": 256,
        "listar": 8192,
        "retro": 4096,
        "validation": 2048,
        "grading_json": 1024,
    }
    for kind, n in expected_tokens.items():
        assert grading_config.chat_completion_limit_kwargs(kind=kind) == {
            "max_completion_tokens": n
        }


def test_chat_completion_limit_kwargs_desde_env(monkeypatch):
    monkeypatch.setenv("GRADER_MAX_COMPLETION_RETRO", "512")
    assert grading_config.max_completion_tokens_retro() == 512
    assert grading_config.chat_completion_limit_kwargs(kind="retro") == {
        "max_completion_tokens": 512
    }


def test_chat_completion_limit_kwargs_kind_invalid():
    with pytest.raises(ValueError, match="kind"):
        grading_config.chat_completion_limit_kwargs(kind="invalid")  # type: ignore[arg-type]


def test_max_completion_tokens_env_no_numerico_usa_default(monkeypatch):
    monkeypatch.setenv("GRADER_MAX_COMPLETION_ESCALA", "x")
    assert grading_config.max_completion_tokens_escala() == 256
