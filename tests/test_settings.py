import logging

import pytest

from grader_agent import settings


def test_llm_model_prefers_llm_model_over_grader_chat(monkeypatch):
    monkeypatch.setenv("LLM_MODEL", "gpt-4.1")
    monkeypatch.setenv("GRADER_CHAT_MODEL", "gpt-4o")
    assert settings.llm_model() == "gpt-4.1"
    assert settings.chat_model() == "gpt-4.1"


def test_llm_model_falls_back_to_grader_chat_when_llm_model_empty(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.setenv("GRADER_CHAT_MODEL", "gpt-4o-mini")
    assert settings.llm_model() == "gpt-4o-mini"


def test_llm_model_default_when_both_empty(monkeypatch):
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("GRADER_CHAT_MODEL", raising=False)
    assert settings.llm_model() == "gpt-4o"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("", False),
        ("0", False),
        ("false", False),
        ("1", True),
        ("true", True),
        ("YES", True),
    ],
)
def test_skip_llm_validation(monkeypatch, raw, expected):
    monkeypatch.setenv("SKIP_LLM_VALIDATION", raw)
    assert settings.skip_llm_validation() is expected


def test_validation_llm_model_default(monkeypatch):
    monkeypatch.delenv("VALIDATION_LLM_MODEL", raising=False)
    assert settings.validation_llm_model() == "gpt-4o-mini"


def test_openrouter_base_url_constant():
    assert settings.openrouter_base_url() == "https://openrouter.ai/api/v1"


def test_log_level_invalid_and_blank(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "NO_SUCH_LEVEL")
    assert settings.log_level() == logging.INFO
    monkeypatch.setenv("LOG_LEVEL", "   ")
    assert settings.log_level() == logging.INFO


def test_grading_token_defaults(monkeypatch):
    monkeypatch.delenv("GRADING_MAX_TOKENS", raising=False)
    monkeypatch.delenv("FEEDBACK_MAX_TOKENS", raising=False)
    monkeypatch.delenv("VALIDATION_MAX_TOKENS", raising=False)
    assert settings.grading_max_tokens() == 8192
    assert settings.feedback_max_tokens() == 4096
    assert settings.validation_max_tokens() == 2048


def test_log_file_path_none_when_empty(monkeypatch):
    monkeypatch.delenv("LOG_FILE_PATH", raising=False)
    assert settings.log_file_path() is None
