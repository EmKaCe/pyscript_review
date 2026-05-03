"""Dataclasses for hot-path review session state.

These models are used with ReactiveDict in the PuePy two-state architecture.
Dataclasses are preferred over Pydantic here for performance in hot-path state.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CategorySelections:
    """Selection state for a single rubric category."""

    checked_items: list[str] = field(
        default_factory=list,
        metadata={"description": "Checked sub-point identifiers for this category"},
    )
    notes: str = field(
        default="",
        metadata={"description": "Free-form additional notes for the category"},
    )


@dataclass
class ReviewSession:
    """Complete review session representing an in-progress or saved review."""

    student_id: str = field(
        default="",
        metadata={"description": "Student identifier, e.g. '2026SS_42'"},
    )
    assignment_id: str = field(
        default="",
        metadata={"description": "Assignment this review belongs to"},
    )
    category_selections: dict[str, CategorySelections] = field(
        default_factory=dict,
        metadata={
            "description": "Per-category selections keyed by category slug",
        },
    )
    grading_inputs: dict[str, float] = field(
        default_factory=dict,
        metadata={"description": "Raw scores entered for each grading dimension"},
    )
    generated_text: str = field(
        default="",
        metadata={"description": "Generated evaluation text from rubric selections"},
    )
    metadata: dict[str, str] = field(
        default_factory=dict,
        metadata={"description": "Additional metadata key-value pairs"},
    )
