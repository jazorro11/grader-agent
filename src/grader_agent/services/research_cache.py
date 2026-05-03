"""On-disk cache for rubric research guides keyed by rubric content hash.

The researcher agent runs once per rubric content (``RubricResearchService``)
and stores both the human-readable Markdown guide and a JSON sidecar with
the structured payload (citations and warnings). Subsequent grading runs
look the guide up by SHA-256 of the normalized rubric body and reuse it.

Cache layout, under ``GraderPaths.research_dir`` (default ``data/research``):

- ``<hash>.md``   — Markdown guide injected into the grading prompt.
- ``<hash>.json`` — Sidecar with structured payload + metadata.

Corrupted files (e.g. truncated writes after a crash) are treated as cache
misses so the next run regenerates the guide instead of poisoning grading.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from grader_agent.settings import GraderPaths

_logger = logging.getLogger(__name__)

_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class CachedResearch:
    """Snapshot of a cached research guide (Markdown + structured payload)."""

    rubric_hash: str
    guide_markdown: str
    payload: dict[str, Any]


def rubric_hash(rubric_md: str) -> str:
    """SHA-256 hex digest of the rubric content normalized for whitespace.

    Hashing the normalized form makes the cache stable against trivial
    edits (CRLF vs LF, trailing spaces, blank-line churn) so educators do
    not pay for a fresh research call on cosmetic rubric changes.
    """
    normalized = _WHITESPACE_RE.sub(" ", (rubric_md or "")).strip()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return digest


def _research_paths(paths: GraderPaths, hash_hex: str) -> tuple[Path, Path]:
    base = paths.research_dir
    return base / f"{hash_hex}.md", base / f"{hash_hex}.json"


def read_cached(paths: GraderPaths, hash_hex: str) -> CachedResearch | None:
    """Return cached entry for ``hash_hex`` or ``None`` on miss / corruption."""
    md_path, json_path = _research_paths(paths, hash_hex)
    if not md_path.is_file() or not json_path.is_file():
        return None
    try:
        guide_md = md_path.read_text(encoding="utf-8")
        payload_raw = json_path.read_text(encoding="utf-8")
        payload = json.loads(payload_raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        _logger.warning(
            "research_cache corrupt entry hash=%s err=%s; treating as miss",
            hash_hex,
            exc,
        )
        return None
    if not isinstance(payload, dict):
        return None
    if not guide_md.strip():
        return None
    return CachedResearch(
        rubric_hash=hash_hex,
        guide_markdown=guide_md,
        payload=payload,
    )


def write_cached(
    paths: GraderPaths,
    hash_hex: str,
    *,
    guide_markdown: str,
    payload: dict[str, Any],
) -> None:
    """Atomically persist a research guide and its structured payload."""
    paths.research_dir.mkdir(parents=True, exist_ok=True)
    md_path, json_path = _research_paths(paths, hash_hex)

    metadata = dict(payload)
    metadata.setdefault("rubric_hash", hash_hex)

    _atomic_write_text(md_path, guide_markdown)
    _atomic_write_text(json_path, json.dumps(metadata, ensure_ascii=False, indent=2))


def delete_cached(paths: GraderPaths, hash_hex: str) -> bool:
    """Remove cached entry for ``hash_hex``; return True if anything was deleted."""
    md_path, json_path = _research_paths(paths, hash_hex)
    removed = False
    for path in (md_path, json_path):
        try:
            path.unlink()
            removed = True
        except FileNotFoundError:
            continue
        except OSError as exc:
            _logger.warning("research_cache could not unlink %s err=%s", path, exc)
    return removed


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


__all__ = [
    "CachedResearch",
    "delete_cached",
    "read_cached",
    "rubric_hash",
    "write_cached",
]
