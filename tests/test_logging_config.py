import logging

from grader_agent.logging_config import (
    RequestIdFilter,
    bind_request_id,
    configure_root_logging,
    reset_request_id,
)
from grader_agent.settings import log_level


def test_request_id_filter_uses_context_default():
    filt = RequestIdFilter()
    record = logging.LogRecord("m", logging.INFO, __file__, 1, "hello", (), None)
    assert filt.filter(record) is True
    assert record.request_id == "-"


def test_request_id_filter_reflects_bound_value():
    filt = RequestIdFilter()
    record = logging.LogRecord("m", logging.INFO, __file__, 1, "hello", (), None)
    token = bind_request_id("req-abc")
    try:
        assert filt.filter(record) is True
        assert record.request_id == "req-abc"
    finally:
        reset_request_id(token)


def test_log_level_from_settings(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    assert log_level() == logging.WARNING


def test_configure_root_logging_updates_level_on_repeat_call(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    root = logging.getLogger()
    configure_root_logging()
    assert root.level == logging.DEBUG
    monkeypatch.setenv("LOG_LEVEL", "CRITICAL")
    configure_root_logging()
    assert root.level == logging.CRITICAL
