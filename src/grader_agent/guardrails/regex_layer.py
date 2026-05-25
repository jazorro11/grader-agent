"""
Deterministic regex layer for obvious prompt-injection and obfuscation signals.

No tokens consumed; returns named attack categories for each match.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RegexContentScanResult:
    """One deterministic hit from :func:`scan_text_for_policy_violations`."""

    attack_type: str
    excerpt: str


# Whisper / policy scanning uses the full submission text; keep excerpts short.
_EXCERPT_MAX = 120


def _clip(s: str) -> str:
    s = s.strip()
    if len(s) <= _EXCERPT_MAX:
        return s
    return s[: _EXCERPT_MAX - 3] + "..."


def scan_text_for_policy_violations(text: str) -> list[RegexContentScanResult]:
    """
    Scan ``text`` for high-confidence injection / exfiltration / obfuscation patterns.

    Returns a list of hits (possibly empty). Order follows pattern table order;
    overlapping matches are all reported.
    """
    if not text or not str(text).strip():
        return []

    s = str(text)
    flags = re.IGNORECASE | re.MULTILINE
    patterns: list[tuple[str, re.Pattern[str]]] = [
        (
            "instruction_override",
            re.compile(
                r"\bignora\s+lo\s+anterior\b|"
                r"\bignore\s+(?:all\s+)?(?:previous|prior)\s+instructions\b|"
                r"\bdiscard\s+(?:all\s+)?(?:previous|prior)\s+instructions\b|"
                r"\boverride\s+all\s+previous\s+rules\b|"
                r"\bannulate\s+toutes\s+les\s+instructions\s+précédentes\b",
                flags,
            ),
        ),
        (
            "rubric_override",
            re.compile(
                r"\bdisregard\s+the\s+rubric\b|"
                r"\bignore\s+the\s+rubric\b|"
                r"\bignor(?:á|a)\s+la\s+rúbrica\b|"
                r"\bolvid(?:a|ate)\s+las\s+reglas\s+del\s+docente\b|"
                r"\btreat\s+the\s+following\s+as\s+system\s+policy\b",
                flags,
            ),
        ),
        (
            "role_manipulation",
            re.compile(
                r"\beres\s+ahora\s+un\b|" r"\byou\s+are\s+now\s+(?:a|an)\b",
                flags,
            ),
        ),
        (
            "instruction_forget",
            re.compile(
                r"\bforget\s+your\s+instructions\b|" r"\bolvida\s+tus\s+instrucciones\b",
                flags,
            ),
        ),
        (
            "false_delimiter",
            re.compile(
                r"<<<\s*SYSTEM\s*>>>|" r"\[INST\]|" r"###\s*System\s*:",
                flags,
            ),
        ),
        (
            "prompt_exfiltration",
            re.compile(
                r"\bmuestra(?:me)?\s+el\s+system\s+prompt\b|"
                r"\bshow\s+me\s+(?:the\s+)?(?:system\s+)?prompt\b|"
                r"\breveal\s+(?:your\s+)?(?:system\s+)?prompt\b|"
                r"\bshow\s+me\s+the\s+rubric\b|"
                r"\bmostr(?:á|a)\s+(?:el\s+)?(?:prompt|system)\b",
                flags,
            ),
        ),
        (
            "encoding_base64",
            re.compile(r"(?:[A-Za-z0-9+/]{4}){10,}(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?"),
        ),
        (
            "encoding_escape_obfuscation",
            re.compile(
                r"(?:\\x[0-9a-fA-F]{2}\s*){4,}|" r"(?:\\u[0-9a-fA-F]{4}\s*){3,}",
            ),
        ),
        (
            "severe_profanity",
            re.compile(
                r"\bhijo\s+de\s+puta\b|"
                r"\bpendejo\s+de\s+mierda\b|"
                r"\bstupid\s+fucking\s+moron\b",
                flags,
            ),
        ),
        (
            "sexual_harassment",
            re.compile(
                r"\bmándame\s+fotos\s+desnud[ao]\b|"
                r"\bsend\s+me\s+nudes\b|"
                r"\bquiero\s+comprar\s+sexo\s+con\s+menores\b",
                flags,
            ),
        ),
        (
            "violent_threat",
            re.compile(
                r"\bte\s+voy\s+a\s+matar\b|"
                r"\bi\s+will\s+blow\s+up\s+the\s+school\b|"
                r"\blos\s+profesores\s+deberían\s+ser\s+ejecutados\s+en\s+público\b",
                flags,
            ),
        ),
    ]

    out: list[RegexContentScanResult] = []
    seen_spans: set[tuple[int, int, str]] = set()
    for attack_type, rx in patterns:
        for m in rx.finditer(s):
            key = (m.start(), m.end(), attack_type)
            if key in seen_spans:
                continue
            seen_spans.add(key)
            out.append(RegexContentScanResult(attack_type=attack_type, excerpt=_clip(m.group(0))))
    return out


__all__ = ["RegexContentScanResult", "scan_text_for_policy_violations"]
