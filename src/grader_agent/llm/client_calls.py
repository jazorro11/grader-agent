"""Shared OpenAI chat completion calls with JSON object responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from grader_agent.grading_config import CompletionKind, chat_completion_limit_kwargs
from grader_agent.openai_retry import with_transient_api_retry

if TYPE_CHECKING:
    from openai import OpenAI


def chat_completion_json_content(
    client: OpenAI,
    *,
    model: str,
    system: str,
    user: str,
    temperature: float,
    kind: CompletionKind,
) -> str:
    """
    Run a chat completion with ``response_format=json_object`` and return message text.

    Raises:
        ValueError: if the model returns empty or non-string content.
    """
    response = with_transient_api_retry(
        lambda: client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
            **chat_completion_limit_kwargs(kind=kind),
        ),
        max_attempts=3,
    )
    if not response.choices:
        raise ValueError(
            "The grading model returned no choices (empty response). "
            "Try again or check your rubric and API status."
        )
    raw = response.choices[0].message.content
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(
            "The grading model returned an empty message. "
            "Try again, increase token limits (GRADER_MAX_COMPLETION_*), or simplify the rubric."
        )
    return raw
