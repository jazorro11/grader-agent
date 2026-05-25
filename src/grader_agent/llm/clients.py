"""OpenAI SDK clients: OpenRouter (chat) and OpenAI (Whisper only)."""

from __future__ import annotations

from functools import lru_cache

from openai import OpenAI


def make_openrouter_chat_client(
    *,
    api_key: str,
    base_url: str | None = None,
) -> OpenAI:
    """
    Chat-completions client via OpenRouter (grading, feedback, validation, etc.).

    Uses the official OpenAI Python SDK with a custom ``base_url``.
    When ``base_url`` is omitted, :func:`grader_agent.settings.openrouter_base_url` is used.
    """
    from grader_agent.settings import openrouter_base_url

    resolved = openrouter_base_url() if base_url is None else base_url
    return OpenAI(base_url=resolved, api_key=api_key)


def make_openai_transcription_client(*, api_key: str) -> OpenAI:
    """
    Direct OpenAI client for audio transcription (Whisper) only — default API host.
    """
    return OpenAI(api_key=api_key)


@lru_cache(maxsize=1)
def get_default_openrouter_chat_client() -> OpenAI:
    """Process-wide OpenRouter client from ``OPENROUTER_API_KEY`` (grading modules)."""
    from grader_agent.settings import openrouter_api_key

    key = openrouter_api_key()
    if not key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Copy `.env.example` to `.env` and add your key."
        )
    return make_openrouter_chat_client(api_key=key)


@lru_cache(maxsize=1)
def get_default_openai_transcription_client() -> OpenAI:
    """Process-wide OpenAI client from ``OPENAI_API_KEY`` (Whisper only)."""
    from grader_agent.settings import openai_api_key

    key = openai_api_key()
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set. Copy `.env.example` to `.env` and add your key."
        )
    return make_openai_transcription_client(api_key=key)
