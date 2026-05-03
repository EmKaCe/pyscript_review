"""Dataclasses for IndexedDB serialization and export.

These models define the shape of data persisted in the browser's IndexedDB
storage and JSON export files.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ReviewRecord:
    """A persisted review record saved in IndexedDB."""

    id: str = field(
        metadata={"description": "Unique record identifier"},
    )
    student_id: str = field(
        metadata={"description": "Student identifier, e.g. '2026SS_42'"},
    )
    assignment_id: str = field(
        metadata={"description": "Assignment this review belongs to"},
    )
    semester: str = field(
        metadata={"description": "Academic semester derived from student identifier"},
    )
    category_selections: dict = field(
        metadata={"description": "Serialized category selections as a dict"},
    )
    grading_inputs: dict = field(
        metadata={"description": "Serialized grading inputs as a dict"},
    )
    grade_result: dict = field(
        metadata={"description": "Serialized grade result as a dict"},
    )
    created_at: str = field(
        metadata={"description": "ISO timestamp when the review was first created"},
    )
    updated_at: str = field(
        metadata={"description": "ISO timestamp of the last update"},
    )
    generated_text: str = field(
        default="",
        metadata={
            "description": "Generated evaluation text from rubric selections",
        },
    )


@dataclass
class CurrentSessionRecord:
    """Special record for the auto-saved in-progress session.

    This record uses a fixed sentinel key ``__current__`` in IndexedDB
    so the review list never shows half-finished drafts.
    """

    data: dict = field(
        metadata={"description": "Full serialized session state as a dict"},
    )
    id: str = field(
        default="__current__",
        metadata={
            "description": "Fixed sentinel value identifying the current session",
        },
    )


@dataclass
class DbExport:
    """Structure of a bulk export containing all persisted reviews."""

    version: int = field(
        metadata={"description": "Schema version of the export format"},
    )
    exported_at: str = field(
        metadata={"description": "ISO timestamp when the export was generated"},
    )
    reviews: list[ReviewRecord] = field(
        metadata={"description": "All review records included in the export"},
    )
