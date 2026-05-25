"""3.3 — Content validation: regex layer (A) + optional LLM layer (B)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from grader_agent.grading.llm_json import json_object_from_message_content
from grader_agent.guardrails.regex_layer import scan_text_for_policy_violations
from grader_agent.llm.client_calls import chat_completion_json_content
from grader_agent.models import ContentValidationResult
from grader_agent.prompts_loader import system_prompt_validacion_capa_b
from grader_agent.settings import skip_llm_validation, validation_llm_model

if TYPE_CHECKING:
    from openai import OpenAI

_logger = logging.getLogger(__name__)


class LlmContentValidationLayer:
    """Layer B: OpenRouter JSON verdict (only when regex layer is clean)."""

    def __init__(self, openrouter_client: OpenAI) -> None:
        """Client used for ``VALIDATION_LLM_MODEL`` JSON completions."""
        self._client = openrouter_client

    def analyze(self, text: str, *, request_id: str | None = None) -> ContentValidationResult:
        """
        Llama al modelo de validación con prompt de capa B y mapea ``veredicto`` a clean/rejected.

        Ante excepciones de red/API o JSON inesperado devuelve veredicto ``rejected``.
        """
        if request_id:
            _logger.debug("llm_validation request_id=%s", request_id)
        user = f"TEXTO A ANALIZAR (entre delimitadores):\n<<<STUDENT>>>\n{text}\n<<<END>>>"
        try:
            raw = chat_completion_json_content(
                self._client,
                model=validation_llm_model(),
                system=system_prompt_validacion_capa_b(),
                user=user,
                temperature=0,
                kind="validation",
            )
        except Exception as exc:
            _logger.warning("LLM content validation failed: %s", exc)
            return ContentValidationResult(
                verdict="rejected",
                reason="No se pudo completar la validación automática del contenido.",
                flagged_patterns=("llm_error",),
                detection_layer="llm",
            )

        data = json_object_from_message_content(raw)
        verdict_raw = data.get("veredicto")
        if isinstance(verdict_raw, str):
            verdict_norm = verdict_raw.strip().lower()
        else:
            verdict_norm = ""

        razon = data.get("razon")
        reason = str(razon).strip() if razon is not None else ""

        patrones = data.get("patrones_detectados")
        patterns: tuple[str, ...] = ()
        if isinstance(patrones, list):
            patterns = tuple(str(p).strip() for p in patrones if str(p).strip())

        if verdict_norm == "clean":
            return ContentValidationResult(
                verdict="clean",
                reason=reason or "Sin hallazgos en la capa LLM.",
                flagged_patterns=patterns,
                detection_layer="llm",
            )
        if verdict_norm == "rejected":
            return ContentValidationResult(
                verdict="rejected",
                reason=reason or "Contenido rechazado por la validación LLM.",
                flagged_patterns=patterns or ("llm_rejected",),
                detection_layer="llm",
            )

        _logger.warning("Unexpected LLM validation JSON: %s", data)
        return ContentValidationResult(
            verdict="rejected",
            reason="Respuesta inválida del validador LLM.",
            flagged_patterns=("invalid_llm_json",),
            detection_layer="llm",
        )


class ContentValidationService:
    """Runs regex (A) then optional LLM (B) unless ``SKIP_LLM_VALIDATION`` is true."""

    def __init__(self, openrouter_client: OpenAI) -> None:
        """``openrouter_client`` backs layer B when layer A (regex) is clean."""
        self._llm = LlmContentValidationLayer(openrouter_client)

    def validate(self, text: str, *, request_id: str | None = None) -> ContentValidationResult:
        """
        Paso 2: ejecuta capa regex; si no hay coincidencias, capa LLM salvo ``SKIP_LLM_VALIDATION``.
        """
        if request_id:
            _logger.debug("content_validation request_id=%s", request_id)
        hits = scan_text_for_policy_violations(text)
        if hits:
            names = tuple(h.attack_type for h in hits)
            preview = "; ".join(f"{h.attack_type}: {h.excerpt!r}" for h in hits[:5])
            if len(hits) > 5:
                preview = f"{preview}…" if preview else "…"
            reason = "Se detectaron señales de riesgo con reglas determinísticas."
            if preview:
                reason = f"{reason} Detalle: {preview}"
            return ContentValidationResult(
                verdict="rejected",
                reason=reason,
                flagged_patterns=names,
                detection_layer="regex",
            )

        if skip_llm_validation():
            return ContentValidationResult(
                verdict="clean",
                reason="Capa regex sin hallazgos; validación LLM omitida (SKIP_LLM_VALIDATION).",
                flagged_patterns=(),
                detection_layer="regex_only",
            )

        return self._llm.analyze(text, request_id=request_id)


__all__ = ["ContentValidationService", "LlmContentValidationLayer"]
