import httpx
import pytest
from openai import APIStatusError, RateLimitError

from grader_agent.openai_retry import (
    is_transient_api_error,
    openai_api_error_code,
    with_openai_rate_limit_retry,
    with_transient_api_retry,
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
                body={
                    "error": {
                        "code": "rate_limit_exceeded",
                        "message": "Please try again in 100ms.",
                    }
                },
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


def test_transient_retry_503_then_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: None)
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")
    calls = {"n": 0}

    def op() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise APIStatusError("server", response=httpx.Response(503, request=req), body=None)
        return "ok"

    assert with_transient_api_retry(op, max_attempts=3) == "ok"
    assert calls["n"] == 2


def test_transient_retry_401_no_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("grader_agent.openai_retry.time.sleep", lambda s: None)
    req = httpx.Request("POST", "https://api.openai.com/v1/chat/completions")

    def op() -> str:
        raise APIStatusError("denied", response=httpx.Response(401, request=req), body=None)

    with pytest.raises(APIStatusError):
        with_transient_api_retry(op, max_attempts=3)


def test_is_transient_api_error() -> None:
    req = httpx.Request("POST", "https://api.openai.com/v1/x")
    e401 = APIStatusError("x", response=httpx.Response(401, request=req), body=None)
    e503 = APIStatusError("x", response=httpx.Response(503, request=req), body=None)
    assert is_transient_api_error(e401) is False
    assert is_transient_api_error(e503) is True


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
