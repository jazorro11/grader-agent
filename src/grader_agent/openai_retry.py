from __future__ import annotations

import os
import re
import time
from collections.abc import Callable
from typing import TypeVar

from openai import APIStatusError, RateLimitError

T = TypeVar("T")

_TRY_AGAIN_MS = re.compile(r"try again in (\d+)ms", re.IGNORECASE)

_DEFAULT_MAX_RETRIES = 8
_MAX_RETRY_DELAY_S = 60.0
_MAX_RETRY_ATTEMPTS_CAP = 30


def _nested_error_dict(body: object | None) -> dict | None:
    if not isinstance(body, dict):
        return None
    err = body.get("error")
    return err if isinstance(err, dict) else None


def openai_api_error_code(exc: APIStatusError) -> str | None:
    nested = _nested_error_dict(exc.body)
    if nested:
        code = nested.get("code")
        if isinstance(code, str):
            return code
    if isinstance(exc.body, dict):
        code = exc.body.get("code")
        if isinstance(code, str):
            return code
    return None


def _is_insufficient_quota(exc: RateLimitError) -> bool:
    if openai_api_error_code(exc) == "insufficient_quota":
        return True
    nested = _nested_error_dict(exc.body)
    if nested and nested.get("type") == "insufficient_quota":
        return True
    return False


def _retry_delay_seconds(attempt: int, exc: RateLimitError) -> float:
    for text in (exc.message, str(exc.body) if exc.body is not None else ""):
        if text:
            m = _TRY_AGAIN_MS.search(text)
            if m:
                ms = int(m.group(1))
                delay = max(ms / 1000.0, 0.05) + 0.05
                return min(delay, _MAX_RETRY_DELAY_S)
    base = 0.5 * (2 ** min(attempt, 5))
    return min(base, _MAX_RETRY_DELAY_S)


def _max_retries_from_env() -> int:
    raw = os.getenv("OPENAI_RATE_LIMIT_MAX_RETRIES", str(_DEFAULT_MAX_RETRIES))
    try:
        n = int(raw)
    except ValueError:
        return _DEFAULT_MAX_RETRIES
    return max(0, min(n, _MAX_RETRY_ATTEMPTS_CAP))


def with_openai_rate_limit_retry(operation: Callable[[], T], *, max_retries: int | None = None) -> T:
    """
    Ejecuta ``operation`` reintentando solo ante RateLimitError (429) por TPM/RPM,
    no ante ``insufficient_quota`` (facturación).
    """
    if max_retries is None:
        retries = _max_retries_from_env()
    else:
        retries = max(0, min(max_retries, _MAX_RETRY_ATTEMPTS_CAP))
    last: RateLimitError | None = None
    for attempt in range(retries + 1):
        try:
            return operation()
        except RateLimitError as e:
            last = e
            if _is_insufficient_quota(e):
                raise
            if attempt >= retries:
                raise
            time.sleep(_retry_delay_seconds(attempt, e))
    assert last is not None
    raise last
