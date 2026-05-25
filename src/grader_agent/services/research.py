"""Rubric research agent (analytical, official/academic-source-bound).

The service runs once per rubric content (cached via
``research_cache``). It calls a chat model with web-browsing capability
(default ``openai/gpt-4o:online`` on OpenRouter) to enumerate the topics
the rubric evaluates and produce verifiable facts plus citations from
official or academic sources only.

The output is a Markdown guide (``CachedResearch.guide_markdown``) that
the grading service injects as additional context in step 4 of the
pipeline. Citations whose hostname does not match the configured
allowlist are filtered out before rendering.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from grader_agent.grading.llm_json import json_object_from_message_content
from grader_agent.llm.client_calls import chat_completion_json_content
from grader_agent.models import ERROR_TYPE_INTERNAL, ERROR_TYPE_OPENAI, ErrorResult
from grader_agent.prompts_loader import system_prompt_investigador_rubrica
from grader_agent.services.research_cache import (
    CachedResearch,
    delete_cached,
    read_cached,
    rubric_hash,
    write_cached,
)
from grader_agent.settings import (
    GraderPaths,
    research_domain_allowlist,
    research_model,
    skip_research,
)

if TYPE_CHECKING:
    from openai import OpenAI

_logger = logging.getLogger(__name__)


GUIDE_HEADING: str = "# Guía de investigación (fuentes oficiales/académicas)"


class RubricResearchService:
    """Builds and caches a citation-bound research guide for a rubric."""

    def __init__(
        self,
        openrouter_client: OpenAI,
        *,
        paths: GraderPaths | None = None,
    ) -> None:
        """Wire the OpenRouter client used for the ``:online`` research call."""
        self._client = openrouter_client
        self._paths = paths

    def _resolve_paths(self) -> GraderPaths:
        if self._paths is not None:
            return self._paths
        paths = GraderPaths.from_env()
        paths.ensure_directories()
        return paths

    def get_or_create(
        self,
        rubric_md: str,
        *,
        request_id: str | None = None,
        force_refresh: bool = False,
    ) -> CachedResearch | ErrorResult:
        """Return cached guide or run the researcher and persist the result.

        When ``SKIP_RESEARCH`` is truthy the service short-circuits with an
        ``ErrorResult`` so callers can degrade gracefully without invoking
        the model.
        """
        if skip_research():
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="Investigación deshabilitada por SKIP_RESEARCH.",
                detail=None,
            )
        if not (rubric_md or "").strip():
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="No se puede investigar una rúbrica vacía.",
                detail=None,
            )

        paths = self._resolve_paths()
        hash_hex = rubric_hash(rubric_md)

        if force_refresh:
            delete_cached(paths, hash_hex)
        else:
            cached = read_cached(paths, hash_hex)
            if cached is not None:
                _logger.info(
                    "research_cache hit hash=%s request_id=%s",
                    hash_hex,
                    request_id,
                )
                return cached

        result = self.investigate(rubric_md, request_id=request_id)
        if isinstance(result, ErrorResult):
            return result

        guide_md, payload = result
        write_cached(paths, hash_hex, guide_markdown=guide_md, payload=payload)
        return CachedResearch(
            rubric_hash=hash_hex,
            guide_markdown=guide_md,
            payload=payload,
        )

    def investigate(
        self,
        rubric_md: str,
        *,
        request_id: str | None = None,
    ) -> tuple[str, dict[str, Any]] | ErrorResult:
        """Call the researcher model and return ``(guide_markdown, payload)``.

        ``payload`` retains the structured response with filtered citations,
        suitable for persisting alongside the Markdown guide.
        """
        if request_id:
            _logger.debug("research_call request_id=%s", request_id)

        user_message = f"RÚBRICA (Markdown):\n\n{rubric_md.strip()}\n"

        try:
            raw = chat_completion_json_content(
                self._client,
                model=research_model(),
                system=system_prompt_investigador_rubrica(),
                user=user_message,
                temperature=0,
                kind="research",
            )
        except Exception as exc:
            _logger.exception("research chat completion failed")
            return ErrorResult(
                error_type=ERROR_TYPE_OPENAI,
                message="Falló la llamada al agente investigador.",
                detail=str(exc),
            )

        data = json_object_from_message_content(raw)
        normalized = _normalize_payload(data)
        if normalized is None:
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message="El investigador devolvió JSON inválido o vacío.",
                detail="Reintentar la investigación.",
            )

        allowlist = research_domain_allowlist()
        filtered = _filter_payload_citations(normalized, allowlist)
        if not filtered["temas"]:
            return ErrorResult(
                error_type=ERROR_TYPE_INTERNAL,
                message=(
                    "El investigador no devolvió temas con fuentes oficiales/académicas."
                ),
                detail="Revisar la lista de dominios permitidos o reintentar.",
            )

        guide_md = render_guide_markdown(filtered)
        return guide_md, filtered


def _normalize_payload(data: dict[str, Any]) -> dict[str, Any] | None:
    """Coerce the model output to the documented schema; reject if unusable."""
    if not isinstance(data, dict):
        return None
    raw_temas = data.get("temas")
    if not isinstance(raw_temas, list) or not raw_temas:
        return None

    temas: list[dict[str, Any]] = []
    for entry in raw_temas:
        if not isinstance(entry, dict):
            continue
        nombre = str(entry.get("tema") or "").strip()
        if not nombre:
            continue
        hechos = [
            str(h).strip()
            for h in entry.get("hechos") or []
            if isinstance(h, str) and str(h).strip()
        ]
        if not hechos:
            continue
        errores = [
            str(e).strip()
            for e in entry.get("errores_frecuentes") or []
            if isinstance(e, str) and str(e).strip()
        ]
        citas: list[dict[str, str]] = []
        for cita in entry.get("citas") or []:
            if not isinstance(cita, dict):
                continue
            url = str(cita.get("url") or "").strip()
            titulo = str(cita.get("titulo") or "").strip()
            tipo_raw = str(cita.get("tipo") or "").strip().lower()
            if not url or not titulo:
                continue
            tipo = tipo_raw if tipo_raw in {"oficial", "academica"} else "oficial"
            citas.append({"url": url, "titulo": titulo, "tipo": tipo})
        temas.append(
            {
                "tema": nombre,
                "hechos": hechos,
                "errores_frecuentes": errores,
                "citas": citas,
            }
        )

    if not temas:
        return None

    advertencias = [
        str(a).strip()
        for a in data.get("advertencias") or []
        if isinstance(a, str) and str(a).strip()
    ]

    return {"temas": temas, "advertencias": advertencias}


def _filter_payload_citations(
    payload: dict[str, Any],
    allowlist: tuple[str, ...],
) -> dict[str, Any]:
    """Return a copy of ``payload`` with disallowed citations stripped.

    The function rebuilds the ``temas`` list — topics whose citations are all
    rejected and that lack ``hechos`` are removed — and reassigns the new list
    on the input dict (so callers see the filtered view). It does not deep-copy
    advertencias or other top-level fields.
    """
    new_temas: list[dict[str, Any]] = []
    for tema in payload.get("temas", []):
        kept = [c for c in tema.get("citas", []) if _citation_allowed(c.get("url", ""), allowlist)]
        if not kept and not tema.get("hechos"):
            continue
        new_temas.append(
            {
                "tema": tema["tema"],
                "hechos": tema.get("hechos", []),
                "errores_frecuentes": tema.get("errores_frecuentes", []),
                "citas": kept,
            }
        )
    payload["temas"] = new_temas
    return payload


def _citation_allowed(url: str, allowlist: tuple[str, ...]) -> bool:
    if not url:
        return False
    try:
        parsed = urlparse(url)
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    if not host:
        return False
    for entry in allowlist:
        e = entry.lower().lstrip(".")
        if not e:
            continue
        if host == e or host.endswith("." + e):
            return True
    return False


def render_guide_markdown(payload: dict[str, Any]) -> str:
    """Render the structured research payload into the Markdown guide."""
    lines: list[str] = [GUIDE_HEADING, ""]
    citations: list[dict[str, str]] = []

    for tema in payload.get("temas", []):
        lines.append(f"## Tema: {tema['tema']}")
        for hecho in tema.get("hechos", []):
            cita_dom = _first_citation_host(tema.get("citas", []))
            suffix = f" [cita: {cita_dom}]" if cita_dom else ""
            lines.append(f"- Hecho: {hecho}{suffix}")
        errores = tema.get("errores_frecuentes", [])
        if errores:
            lines.append("- Errores frecuentes:")
            for err in errores:
                lines.append(f"  - {err}")
        lines.append("")
        citations.extend(tema.get("citas", []))

    advertencias = payload.get("advertencias", [])
    if advertencias:
        lines.append("## Advertencias para el calificador")
        for adv in advertencias:
            lines.append(f"- {adv}")
        lines.append("")

    if citations:
        seen: set[str] = set()
        lines.append("## Citas")
        for cita in citations:
            key = cita["url"]
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"- {cita['titulo']} — {cita['url']} ({cita['tipo']})")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _first_citation_host(citas: list[dict[str, str]]) -> str:
    for cita in citas:
        try:
            host = urlparse(cita.get("url", "")).hostname or ""
        except ValueError:
            host = ""
        if host:
            return host.lower()
    return ""


__all__ = [
    "GUIDE_HEADING",
    "RubricResearchService",
    "render_guide_markdown",
]
