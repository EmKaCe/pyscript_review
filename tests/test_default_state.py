"""Tests for DEFAULT_STATE completeness and correct default values.

Verifies that all required keys are present, new keys have correct defaults,
and that the dict remains the single source of truth for application state.
"""

from __future__ import annotations

from src.state import DEFAULT_STATE


class TestDefaultStateKeys:
    """All required keys exist in DEFAULT_STATE."""

    EXPECTED_KEYS: set[str] = {
        "mode",
        "student_id",
        "assignment_id",
        "category_selections",
        "grading_inputs",
        "generated_text",
        "criteria_bundle",
        "assignments",
        "current_review_id",
        "saved_reviews",
        "can_undo",
        "can_redo",
        "current_semester",
        "semester_list",
        "initialized",
        "notification",
        "theme",
        "sidebar_open",
        "mobile_view",
        "sidebar_collapsed",
        "copy_state",
        "import_state",
        "boot_error",
        "grade_result",
    }

    def test_all_keys_present(self) -> None:
        """Every expected key should be in DEFAULT_STATE."""
        assert self.EXPECTED_KEYS.issubset(set(DEFAULT_STATE.keys()))

    def test_no_extra_keys(self) -> None:
        """DEFAULT_STATE should have exactly the expected keys (no drift)."""
        assert set(DEFAULT_STATE.keys()) == self.EXPECTED_KEYS

    def test_key_count(self) -> None:
        """DEFAULT_STATE should have exactly 24 keys."""
        assert len(DEFAULT_STATE) == 24


class TestDefaultStateMode:
    """Mode defaults to 'teacher'."""

    def test_mode_default_is_teacher(self) -> None:
        """The default mode should be 'teacher'."""
        assert DEFAULT_STATE["mode"] == "teacher"

    def test_mode_is_string(self) -> None:
        """Mode should be a string."""
        assert isinstance(DEFAULT_STATE["mode"], str)


class TestDefaultStateMobileView:
    """mobile_view defaults to 'criteria'."""

    def test_mobile_view_default_is_criteria(self) -> None:
        """The default mobile_view should be 'criteria'."""
        assert DEFAULT_STATE["mobile_view"] == "criteria"

    def test_mobile_view_is_string(self) -> None:
        """mobile_view should be a string."""
        assert isinstance(DEFAULT_STATE["mobile_view"], str)


class TestDefaultStateNewKeys:
    """New keys (sidebar_collapsed, copy_state, import_state) have correct defaults."""

    def test_sidebar_collapsed_default(self) -> None:
        """sidebar_collapsed should default to False."""
        assert DEFAULT_STATE["sidebar_collapsed"] is False

    def test_sidebar_collapsed_is_bool(self) -> None:
        """sidebar_collapsed should be a boolean."""
        assert isinstance(DEFAULT_STATE["sidebar_collapsed"], bool)

    def test_copy_state_default(self) -> None:
        """copy_state should default to empty string."""
        assert DEFAULT_STATE["copy_state"] == ""

    def test_copy_state_is_string(self) -> None:
        """copy_state should be a string."""
        assert isinstance(DEFAULT_STATE["copy_state"], str)

    def test_import_state_default(self) -> None:
        """import_state should default to empty string."""
        assert DEFAULT_STATE["import_state"] == ""

    def test_import_state_is_string(self) -> None:
        """import_state should be a string."""
        assert isinstance(DEFAULT_STATE["import_state"], str)


class TestDefaultStateTypeConsistency:
    """All values have the correct type for their role."""

    def test_dict_values_are_dicts(self) -> None:
        """category_selections and grading_inputs should be dicts."""
        assert isinstance(DEFAULT_STATE["category_selections"], dict)
        assert isinstance(DEFAULT_STATE["grading_inputs"], dict)

    def test_list_values_are_lists(self) -> None:
        """assignments, saved_reviews, semester_list should be lists."""
        assert isinstance(DEFAULT_STATE["assignments"], list)
        assert isinstance(DEFAULT_STATE["saved_reviews"], list)
        assert isinstance(DEFAULT_STATE["semester_list"], list)

    def test_bool_values_are_bools(self) -> None:
        """can_undo, can_redo, initialized, sidebar_open, sidebar_collapsed should be bools."""
        bool_keys = {
            "can_undo",
            "can_redo",
            "initialized",
            "sidebar_open",
            "sidebar_collapsed",
        }
        for key in bool_keys:
            assert isinstance(DEFAULT_STATE[key], bool), f"{key} is not bool"

    def test_none_values(self) -> None:
        """criteria_bundle and current_review_id should default to None."""
        assert DEFAULT_STATE["criteria_bundle"] is None
        assert DEFAULT_STATE["current_review_id"] is None
