"""Application state — DEFAULT_STATE, ReviewState, undo/redo, serialization helpers.

This module provides the central state management for the SciPro review app,
following the PuePy two-state architecture: self.state for UI-local data,
self.application.state for shared business data.

All app-wide state keys must be declared in DEFAULT_STATE. The ReviewState class
wraps a ReactiveDict with convenience methods for checkbox toggling, grading input
management, and undo/redo with a 50-snapshot limit.
"""

from __future__ import annotations

from typing import Any

from puepy.reactivity import ReactiveDict

from src.models.session import CategorySelections, ReviewSession

# ---------------------------------------------------------------------------
# Default application state — ALL app-wide keys declared here.
# ---------------------------------------------------------------------------

DEFAULT_STATE: dict[str, Any] = {
    "mode": "teacher",  # "teacher" or "student"
    "student_id": "",
    "assignment_id": "",
    "category_selections": {},  # dict[str, CategorySelections]
    "grading_inputs": {},  # dict[str, float] (dimension name -> score)
    "generated_text": "",
    "criteria_bundle": None,  # CriteriaBundle | None
    "assignments": [],  # list[AssignmentConfig]
    "current_review_id": None,  # str | None
    "saved_reviews": [],  # list[dict] (serialized ReviewRecord list)
    "can_undo": False,
    "can_redo": False,
    "current_semester": "",  # e.g. "WS2025"
    "semester_list": [],  # list[str]
    "initialized": False,
    "notification": "",  # notification message
    "theme": "light",  # "light" or "dark"
    "sidebar_open": False,
    "mobile_view": "criteria",  # which panel is shown on mobile
    "sidebar_collapsed": False,  # sidebar collapse state
    "copy_state": "",  # clipboard copy state tracking
    "import_state": "",  # import operation state tracking
    "boot_error": None,  # str | None — startup error message
    "grade_result": None,  # GradeResult | None
}

# All grading dimension keys (used for zeroing).
_DIMENSION_KEYS: list[str] = [
    "code_quality_design",
    "code_execution_results",
    "assignment_requirements",
    "scientific_programming",
    "creativity",
]


# ---------------------------------------------------------------------------
# ReviewState — central orchestrator wrapping a ReactiveDict.
# ---------------------------------------------------------------------------


class ReviewState:
    """Wraps a PuePy ReactiveDict with state management, grading, and undo/redo.

    The ReactiveDict is expected to be bound to a PuePy Application's
    `self.application.state`. Mutations through this wrapper update the
    reactive dict in-place, automatically triggering PuePy redraws for
    any components watching the changed keys.

    Undo/redo stores shallow snapshots of category_selections and
    grading_inputs only — NOT the full state dict. Snapshots are serialized
    as plain dicts/lists for safe JSON-style copy semantics.

    Attributes:
        _state: The backing ReactiveDict instance.
        _undo_stack: List of serialized snapshots (oldest first).
        _redo_stack: List of serialized snapshots (oldest first).
    """

    _MAX_UNDO: int = 50

    def __init__(self, state: ReactiveDict) -> None:
        """Initialise the ReviewState wrapper.

        Args:
            state: A ReactiveDict pre-loaded with DEFAULT_STATE values.
        """
        self._state: ReactiveDict = state
        self._undo_stack: list[dict[str, Any]] = []
        self._redo_stack: list[dict[str, Any]] = []

    # -- Convenience accessors -------------------------------------------------

    @property
    def mode(self) -> str:
        return self._state.get("mode", "")

    @mode.setter
    def mode(self, value: str) -> None:
        self._state["mode"] = value

    @property
    def student_id(self) -> str:
        return self._state.get("student_id", "")

    @student_id.setter
    def student_id(self, value: str) -> None:
        self._state["student_id"] = value

    @property
    def assignment_id(self) -> str:
        return self._state.get("assignment_id", "")

    @assignment_id.setter
    def assignment_id(self, value: str) -> None:
        self._state["assignment_id"] = value

    @property
    def category_selections(self) -> dict[str, CategorySelections]:
        return self._state.get("category_selections", {})

    @property
    def grading_inputs(self) -> dict[str, float]:
        return self._state.get("grading_inputs", {})

    @property
    def generated_text(self) -> str:
        return self._state.get("generated_text", "")

    @generated_text.setter
    def generated_text(self, value: str) -> None:
        self._state["generated_text"] = value

    @property
    def can_undo(self) -> bool:
        return bool(self._state.get("can_undo", False))

    @can_undo.setter
    def can_undo(self, value: bool) -> None:
        self._state["can_undo"] = value

    @property
    def can_redo(self) -> bool:
        return bool(self._state.get("can_redo", False))

    @can_redo.setter
    def can_redo(self, value: bool) -> None:
        self._state["can_redo"] = value

    @property
    def notification(self) -> str:
        return self._state.get("notification", "")

    @notification.setter
    def notification(self, value: str) -> None:
        self._state["notification"] = value

    # -- Category progress ----------------------------------------------------
    @property
    def category_progress(self) -> dict[str, int]:
        """Count categories with at least one checked item vs total categories.

        Looks up the current criteria_bundle to determine total categories.
        Only counts categories that have entries in category_selections with
        a non-empty checked_items list.

        Returns:
            A dict with keys "filled" (int) and "total" (int).
        """
        bundle = self._state.get("criteria_bundle")
        total: int = len(bundle.categories) if bundle is not None else 0
        filled: int = 0
        if bundle is not None:
            selections = self.category_selections
            for category in bundle.categories:
                cs = selections.get(category.slug)
                if cs is not None and len(cs.checked_items) > 0:
                    filled += 1
        return {"filled": filled, "total": total}

    def reset_session(self) -> None:
        """Clear all inputs in the current session."""
        self.push_undo()
        self._state["category_selections"] = {}
        self._state["grading_inputs"] = {}
        self._state["generated_text"] = ""
        self._state["student_id"] = ""

    def export_json(self) -> str:
        """Export the current session as a JSON string."""
        import json

        session = self.to_session()
        data = session_to_dict(session)
        return json.dumps(data, indent=2)

    # -- Snapshot helpers ------------------------------------------------------

    def _snapshot(
        self,
    ) -> dict[str, Any]:
        """Build a deep-copied, serialized snapshot of mutable review data.

        Snapshot covers category_selections (serialized to dicts) and
        grading_inputs (dict of float). Both are plain JSON-safe values.

        Returns:
            A dict with keys 'category_selections' and 'grading_inputs'.
        """
        selections: dict[str, dict[str, Any]] = {}
        for key, cs in self.category_selections.items():
            selections[key] = {
                "checked_items": list(cs.checked_items),
                "notes": cs.notes,
            }
        return {
            "category_selections": selections,
            "grading_inputs": dict(self.grading_inputs),
        }

    def _restore_snapshot(self, snapshot: dict[str, Any]) -> None:
        """Restore mutable review state from a snapshot dict.

        Args:
            snapshot: Dict with 'category_selections' and 'grading_inputs' keys.
        """
        selections: dict[str, CategorySelections] = {}
        for key, val in snapshot.get("category_selections", {}).items():
            selections[key] = CategorySelections(
                checked_items=list(val.get("checked_items", [])),
                notes=val.get("notes", ""),
            )
        self._state["category_selections"] = selections
        self._state["grading_inputs"] = dict(snapshot.get("grading_inputs", {}))
        self._state["can_undo"] = len(self._undo_stack) > 0
        self._state["can_redo"] = len(self._redo_stack) > 0

    # -- Undo / redo ----------------------------------------------------------

    def push_undo(self) -> None:
        """Push current review state snapshot onto the undo stack.

        The redo stack is cleared (new action invalidates redo history).
        When the undo stack exceeds _MAX_UNDO (50), the oldest entry is
        evicted.
        """
        self._undo_stack.append(self._snapshot())
        if len(self._undo_stack) > self._MAX_UNDO:
            self._undo_stack.pop(0)
        self._redo_stack.clear()
        self._state["can_undo"] = len(self._undo_stack) > 0
        self._state["can_redo"] = False

    def undo(self) -> None:
        """Revert the last mutable action.

        The current state is pushed onto the redo stack, then the most
        recent undo snapshot is restored.
        """
        if not self._undo_stack:
            return
        self._redo_stack.append(self._snapshot())
        snapshot = self._undo_stack.pop()
        self._restore_snapshot(snapshot)
        self._state["can_undo"] = len(self._undo_stack) > 0
        self._state["can_redo"] = len(self._redo_stack) > 0

    def redo(self) -> None:
        """Re-apply the most recently undone action.

        The current state is pushed onto the undo stack, then the most
        recent redo snapshot is restored.
        """
        if not self._redo_stack:
            return
        self._undo_stack.append(self._snapshot())
        snapshot = self._redo_stack.pop()
        self._restore_snapshot(snapshot)
        self._state["can_undo"] = len(self._undo_stack) > 0
        self._state["can_redo"] = len(self._redo_stack) > 0

    def clear_history(self) -> None:
        """Clear both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._state["can_undo"] = False
        self._state["can_redo"] = False

    # -- Checkbox toggling ----------------------------------------------------

    def toggle_checkbox(self, category_slug: str, point_id: str) -> None:
        """Toggle a checked item for a category.

        If the item is already checked, it is removed. Otherwise it is added.
        If the category does not yet exist in selections, it is created.

        Args:
            category_slug: Slug identifying the rubric category (e.g. 'code_quality').
            point_id: Scoped sub-point identifier, format '{slug}::{sentiment}::{text}'.
        """
        self.push_undo()
        current = self.category_selections.get(category_slug)
        if current is None:
            current = CategorySelections(checked_items=[], notes="")

        checked: list[str] = list(current.checked_items)
        if point_id in checked:
            checked.remove(point_id)
        else:
            checked.append(point_id)

        new_selections = dict(self.category_selections)
        new_selections[category_slug] = CategorySelections(
            checked_items=checked,
            notes=current.notes,
        )
        self._state["category_selections"] = new_selections

    def set_comment(self, category_slug: str, text: str) -> None:
        """Update additional notes for a category.

        Args:
            category_slug: Slug identifying the rubric category.
            text: Comment text to store.
        """
        self.push_undo()
        current = self.category_selections.get(category_slug)
        if current is None:
            current = CategorySelections(checked_items=[], notes="")
        new_selections = dict(self.category_selections)
        new_selections[category_slug] = CategorySelections(
            checked_items=list(current.checked_items),
            notes=text,
        )
        self._state["category_selections"] = new_selections

    # -- Grading inputs -------------------------------------------------------

    def set_grading_input(self, dimension: str, value: float) -> None:
        """Set the raw score for a grading dimension.

        Args:
            dimension: Dimension key (e.g. 'code_quality_design').
            value: Raw score value to set.
        """
        self.push_undo()
        inputs = dict(self.grading_inputs)
        inputs[dimension] = value
        self._state["grading_inputs"] = inputs

    def clear_grading_inputs(self) -> None:
        """Reset all grading dimension scores to zero."""
        self.push_undo()
        self._state["grading_inputs"] = dict.fromkeys(_DIMENSION_KEYS, 0.0)

    # -- Session-level helpers ------------------------------------------------

    def to_session(self) -> ReviewSession:
        """Build a ReviewSession dataclass from the current state.

        Returns:
            A ReviewSession populated from the reactive state.
        """
        return ReviewSession(
            student_id=self.student_id,
            assignment_id=self.assignment_id,
            category_selections=self.category_selections,
            grading_inputs=self.grading_inputs,
            generated_text=self.generated_text,
            metadata={
                "mode": self.mode,
            },
        )

    def load_from_session(self, session: ReviewSession) -> None:
        """Restore state from a ReviewSession instance.

        Args:
            session: The ReviewSession to restore state from.
        """
        self._state["student_id"] = session.student_id
        self._state["assignment_id"] = session.assignment_id
        self._state["category_selections"] = dict(session.category_selections)
        self._state["grading_inputs"] = dict(session.grading_inputs)
        self._state["generated_text"] = session.generated_text
        self._state["mode"] = session.metadata.get("mode", "")


# ---------------------------------------------------------------------------
# Stand-alone serialization helpers
# ---------------------------------------------------------------------------


def session_to_dict(session: ReviewSession) -> dict[str, Any]:
    """Convert a ReviewSession dataclass to a plain serializable dict.

    Ensures CategorySelections dataclass instances are converted to plain
    dicts so the result is safe for IndexedDB or JSON serialization.

    Args:
        session: The ReviewSession to serialize.

    Returns:
        A plain dict representation without dataclass instances.
    """
    selections: dict[str, dict[str, Any]] = {}
    for key, cs in session.category_selections.items():
        selections[key] = {
            "checked_items": list(cs.checked_items),
            "notes": cs.notes,
        }
    return {
        "student_id": session.student_id,
        "assignment_id": session.assignment_id,
        "category_selections": selections,
        "grading_inputs": dict(session.grading_inputs),
        "generated_text": session.generated_text,
        "metadata": dict(session.metadata),
    }


def dict_to_session(data: dict[str, Any]) -> ReviewSession:
    """Rehydrate a plain dict back to a ReviewSession dataclass.

    Handles nested category_selections dicts by converting them back to
    CategorySelections dataclass instances.

    Args:
        data: A plain dict (typically from IndexedDB or JSON deserialization).

    Returns:
        A fully rehydrated ReviewSession.
    """
    selections: dict[str, CategorySelections] = {}
    for key, val in data.get("category_selections", {}).items():
        selections[key] = CategorySelections(
            checked_items=list(val.get("checked_items", [])),
            notes=val.get("notes", ""),
        )
    return ReviewSession(
        student_id=data.get("student_id", ""),
        assignment_id=data.get("assignment_id", ""),
        category_selections=selections,
        grading_inputs=dict(data.get("grading_inputs", {})),
        generated_text=data.get("generated_text", ""),
        metadata=dict(data.get("metadata", {})),
    )


def create_default_state() -> ReactiveDict:
    """Create a fresh ReactiveDict populated with DEFAULT_STATE.

    Returns:
        A new ReactiveDict ready for binding to a PuePy Application.
    """
    return ReactiveDict(dict(DEFAULT_STATE))
