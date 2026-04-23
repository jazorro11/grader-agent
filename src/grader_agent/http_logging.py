# Configuración de logs HTTP para depurar peticiones (método, ruta, status, tiempo).

from __future__ import annotations

import logging
import os
import time

from grader_agent.logging_config import configure_root_logging
from typing import TYPE_CHECKING

from flask import Response

if TYPE_CHECKING:
    from flask import Flask

_LOGGER = logging.getLogger("grader_agent.http")
_ERR = logging.getLogger("grader_agent.errors")


def _post_rule_paths(app: Flask) -> list[str]:
    """Sorted list of POST ``rule`` strings (for 404 hints without dumping bodies)."""
    return sorted(
        {
            str(r.rule)
            for r in app.url_map.iter_rules()
            if "POST" in r.methods and str(r.rule).startswith("/")
        }
    )


def _request_debug_sin_query(request) -> str:
    """Evita volcar tokens o datos en la query string dentro de los logs."""
    nq = len(request.query_string or b"")
    return f"query_bytes={nq}"


def configure_logging() -> None:
    """Configura el root logger (vía ``logging_config``) y opciones de Werkzeug."""
    configure_root_logging()
    if os.environ.get("WERKZEUG_LOG_QUIET", "").lower() in ("1", "true", "yes"):
        logging.getLogger("werkzeug").setLevel(logging.WARNING)


def register_http_logging(app: Flask) -> None:
    """Registra before/after request y manejador 404 con contexto útil."""

    @app.before_request
    def _http_log_start() -> None:
        from flask import g

        g._grader_req_t0 = time.perf_counter()

    @app.after_request
    def _http_log_response(response: Response):
        from flask import g, request

        start = getattr(g, "_grader_req_t0", None)
        elapsed_ms = (time.perf_counter() - start) * 1000 if start is not None else -1.0
        _LOGGER.info(
            "%s %s -> %s (%.1f ms)",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    @app.errorhandler(404)
    def _log_not_found(error):
        from flask import request

        post_paths = _post_rule_paths(app)
        _ERR.warning(
            "404 %s %s | %s | rutas_POST=%s",
            request.method,
            request.path,
            _request_debug_sin_query(request),
            post_paths,
        )
        return error.get_response(request.environ)
