"""
Pipeline data contracts (grading request, outcomes, errors).

These types are the internal boundary between HTTP adapters, grading services,
and persistence. Existing Flask handlers still build plain dicts; future
refactors should map those dicts to/from these structures.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Final, Literal


class DeliveryType(str, Enum):
    """How the submission payload is produced or interpreted."""

    TEXT = "text"
    AUDIO = "audio"
    PDF_DELIVERABLE = "pdf_deliverable"
    CODE_DELIVERABLE = "code_deliverable"


@dataclass
class GradingRequest:
    """
    Normalized input for the grading pipeline.

    ``content`` is the primary submission body (answer text, transcript, or
    policy-defined payload for PDF). Item prompts currently sent as
    ``pregunta`` in HTTP should be embedded by the adapter (for example as
    JSON inside ``content``) until the contract adds an explicit item field.
    """

    delivery_type: DeliveryType
    content: str
    student_name: str
    rubric_content: str


@dataclass
class CriterionScore:
    """Per-criterion score bundle inside a successful ``GradingResult``."""

    score: float
    max_score: float
    feedback: str = ""


@dataclass
class GradingRejection:
    """Structured rejection (e.g. policy, integrity, or moderation)."""

    rejection_reason: str
    warning_note: str | None = None
    flagged_patterns: Sequence[str] = field(default_factory=tuple)
    detection_layer: str = ""


@dataclass
class GradingResult:
    """
    Grading outcome: successful scores or a structured rejection (no scores).

    ``scores_by_criterion`` maps a stable criterion or item label to scores.
    This aligns PDF multi-criterion output; single-item text grading can use
    one entry keyed by the item label. ``feedback`` is overall commentary when
    present (text path); per-criterion text lives on ``CriterionScore.feedback``.

    When ``status`` is ``"rejected"``, ``rejection`` is set and score fields are
    typically empty or zeroed; do not treat as a graded submission.
    """

    scores_by_criterion: Mapping[str, CriterionScore]
    total_score: float
    total_max_score: float
    feedback: str = ""
    student_name: str | None = None
    item_label: str | None = None
    transcription: str | None = None
    deliverable_kind: str | None = None
    id_estudiante: str | None = None
    nombre_completo: str | None = None
    carpeta_origen: str | None = None
    archivo_pdf: str | None = None
    status: Literal["success", "rejected"] = "success"
    rejection: GradingRejection | None = None


@dataclass
class ContentValidationResult:
    """Unified outcome from regex + optional LLM content moderation."""

    verdict: Literal["clean", "rejected"]
    reason: str
    flagged_patterns: Sequence[str] = field(default_factory=tuple)
    detection_layer: str = ""


@dataclass
class ErrorResult:
    """Normalized API or pipeline failure for HTTP mapping."""

    error_type: str
    message: str
    detail: str | None = None


ERROR_TYPE_VALIDATION: Final[str] = "validation"
ERROR_TYPE_OPENAI: Final[str] = "openai"
ERROR_TYPE_INTERNAL: Final[str] = "internal"
ERROR_TYPE_RUBRIC: Final[str] = "rubric_error"

__all__ = [
    "ContentValidationResult",
    "CriterionScore",
    "DeliveryType",
    "ErrorResult",
    "ERROR_TYPE_INTERNAL",
    "ERROR_TYPE_OPENAI",
    "ERROR_TYPE_RUBRIC",
    "ERROR_TYPE_VALIDATION",
    "GradingRejection",
    "GradingRequest",
    "GradingResult",
]
