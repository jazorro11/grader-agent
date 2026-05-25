"""Root logging: timestamp, level, logger name, request_id, message."""

from __future__ import annotations

import contextvars
import logging
from contextvars import Token

from grader_agent.settings import log_file_path, log_level

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


def current_request_id() -> str:
    """Return the correlation id bound in this context (default ``'-'``)."""
    return request_id_ctx.get()


def bind_request_id(value: str) -> Token[str]:
    """Set ``request_id`` for the current context; return token for :func:`reset_request_id`."""
    return request_id_ctx.set(value)


def reset_request_id(token: Token[str]) -> None:
    """Restore the previous ``request_id`` after :func:`bind_request_id`."""
    request_id_ctx.reset(token)


class RequestIdFilter(logging.Filter):
    """Injects ``record.request_id`` for format strings."""

    def filter(self, record: logging.LogRecord) -> bool:
        """Attach ``request_id`` from contextvars so ``%(request_id)s`` formats work."""
        record.request_id = current_request_id()
        return True


def _root_format_string() -> str:
    return "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s"


def configure_root_logging() -> None:
    """
    Configure the root logger once (handlers + format + request_id filter).

    Subsequent calls only update the root level so tests can change ``LOG_LEVEL``.
    """
    root = logging.getLogger()
    level = log_level()
    root.setLevel(level)

    if not root.handlers:
        req_filter = RequestIdFilter()
        fmt = logging.Formatter(_root_format_string(), datefmt="%Y-%m-%d %H:%M:%S")
        stream = logging.StreamHandler()
        stream.addFilter(req_filter)
        stream.setFormatter(fmt)
        root.addHandler(stream)
        path = log_file_path()
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(path, encoding="utf-8")
            file_handler.addFilter(req_filter)
            file_handler.setFormatter(fmt)
            root.addHandler(file_handler)
