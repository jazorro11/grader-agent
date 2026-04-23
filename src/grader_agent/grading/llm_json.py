"""Parseo defensivo de JSON en respuestas chat.completions."""

from __future__ import annotations

import json
from typing import Any


def json_object_from_message_content(content: Any) -> dict:
    """Parse ``content`` as JSON object; return ``{}`` if empty or not a dict."""
    if not isinstance(content, str) or not content.strip():
        return {}
    try:
        out = json.loads(content)
    except json.JSONDecodeError:
        return {}
    return out if isinstance(out, dict) else {}
