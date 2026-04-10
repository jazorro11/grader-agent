import httpx
import pytest
from openai import RateLimitError

from grader_agent.openai_retry import (
    openai_api_error_code,
    with_openai_rate_limit_retry,
)


def _rate_limit_exc(*, message: str, body: dict) -> RateLimitError:
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    resp = httpx.Response(429, request=req)
    return RateLimitError(message, response=resp, body=body)


def test_openai_api_error_code_nested() -> None:
    exc = _rate_limit_exc(
        message="x",
        body={"error": {"code": "rate_limit_exceeded", "message": "m"}},
    )
    assert openai_api_error_code(exc) == "rate_limit_exceeded"


def test_retry_succeeds_after_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: sleeps.append(s))

    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise _rate_limit_exc(
                message="Please try again in 100ms.",
                body={"error": {"code": "rate_limit_exceeded", "message": "Please try again in 100ms."}},
            )
        return "ok"

    assert with_openai_rate_limit_retry(op, max_retries=3) == "ok"
    assert calls["n"] == 2
    assert len(sleeps) == 1
    assert sleeps[0] >= 0.14


def test_insufficient_quota_not_retried(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: sleeps.append(s))

    def op() -> str:
        raise _rate_limit_exc(
            message="quota",
            body={"error": {"code": "insufficient_quota", "type": "insufficient_quota"}},
        )

    with pytest.raises(RateLimitError):
        with_openai_rate_limit_retry(op, max_retries=5)
    assert sleeps == []


def test_exhausted_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: None)

    def op() -> str:
        raise _rate_limit_exc(
            message="limite",
            body={"error": {"code": "rate_limit_exceeded"}},
        )

    with pytest.raises(RateLimitError):
        with_openai_rate_limit_retry(op, max_retries=1)


def test_parsed_delay_capped(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: sleeps.append(s))

    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise _rate_limit_exc(
                message="Please try again in 120000ms.",
                body={"error": {"message": "Please try again in 120000ms."}},
            )
        return "ok"

    assert with_openai_rate_limit_retry(op, max_retries=3) == "ok"
    assert sleeps == [60.0]
