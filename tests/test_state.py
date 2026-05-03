"""Tests for application state management — DEFAULT_STATE, ReviewState, undo/redo."""

from __future__ import annotations

import pytest
from puepy.reactivity import ReactiveDict
from src.models.session import CategorySelections, ReviewSession
from src.state import (
    DEFAULT_STATE,
    ReviewState,
    create_default_state,
    dict_to_session,
    session_to_dict,
)

# ---------------------------------------------------------------------------
# DEFAULT_STATE
# ---------------------------------------------------------------------------


class TestDefaultState:
    """Verify all required keys exist with correct default types."""

    REQUIRED_KEYS: set[str] = {
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
        """Every expected key is present in DEFAULT_STATE."""
        assert set(DEFAULT_STATE.keys()) == self.REQUIRED_KEYS

    def test_key_count(self) -> None:
        """DEFAULT_STATE has exactly 24 top-level keys."""
        assert len(DEFAULT_STATE) == 24

    def test_default_types(self) -> None:
        """Each key holds the expected default type or value."""
        assert DEFAULT_STATE["mode"] == "teacher"
        assert DEFAULT_STATE["student_id"] == ""
        assert DEFAULT_STATE["assignment_id"] == ""
        assert DEFAULT_STATE["category_selections"] == {}
        assert DEFAULT_STATE["grading_inputs"] == {}
        assert DEFAULT_STATE["generated_text"] == ""
        assert DEFAULT_STATE["criteria_bundle"] is None
        assert DEFAULT_STATE["assignments"] == []
        assert DEFAULT_STATE["current_review_id"] is None
        assert DEFAULT_STATE["saved_reviews"] == []
        assert DEFAULT_STATE["can_undo"] is False
        assert DEFAULT_STATE["can_redo"] is False
        assert DEFAULT_STATE["current_semester"] == ""
        assert DEFAULT_STATE["semester_list"] == []
        assert DEFAULT_STATE["initialized"] is False
        assert DEFAULT_STATE["notification"] == ""
        assert DEFAULT_STATE["theme"] == "light"
        assert DEFAULT_STATE["sidebar_open"] is False
        assert DEFAULT_STATE["mobile_view"] == "criteria"
        assert DEFAULT_STATE["sidebar_collapsed"] is False
        assert DEFAULT_STATE["copy_state"] == ""
        assert DEFAULT_STATE["import_state"] == ""


# ---------------------------------------------------------------------------
# create_default_state
# ---------------------------------------------------------------------------


class TestCreateDefaultState:
    """create_default_state() returns a ReactiveDict seeded from DEFAULT_STATE."""

    def test_returns_reactive_dict(self) -> None:
        """Returns a ReactiveDict instance."""
        state = create_default_state()
        assert isinstance(state, ReactiveDict)

    def test_populated_with_defaults(self) -> None:
        """ReactiveDict contains all DEFAULT_STATE keys and values."""
        state = create_default_state()
        for key, expected in DEFAULT_STATE.items():
            assert state.get(key) == expected

    def test_creates_independent_copy(self) -> None:
        """Two calls return independent ReactiveDict instances."""
        a = create_default_state()
        b = create_default_state()
        a["mode"] = "review"
        assert b["mode"] == "teacher"


# ---------------------------------------------------------------------------
# ReviewState — convenience accessors
# ---------------------------------------------------------------------------


class TestReviewStateAccessors:
    """Test property getters/setters on ReviewState."""

    @pytest.fixture
    def state(self) -> ReactiveDict:
        return create_default_state()

    @pytest.fixture
    def review(self, state: ReactiveDict) -> ReviewState:
        return ReviewState(state)

    def test_mode_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.mode == "teacher"
        review.mode = "review"
        assert review.mode == "review"
        assert state["mode"] == "review"

    def test_student_id_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.student_id == ""
        review.student_id = "WS2025_42"
        assert review.student_id == "WS2025_42"
        assert state["student_id"] == "WS2025_42"

    def test_assignment_id_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.assignment_id == ""
        review.assignment_id = "assignment_01"
        assert review.assignment_id == "assignment_01"
        assert state["assignment_id"] == "assignment_01"

    def test_generated_text_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.generated_text == ""
        review.generated_text = "Great work"
        assert review.generated_text == "Great work"
        assert state["generated_text"] == "Great work"

    def test_can_undo_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.can_undo is False
        review.can_undo = True
        assert review.can_undo is True
        assert state["can_undo"] is True

    def test_can_redo_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.can_redo is False
        review.can_redo = True
        assert review.can_redo is True
        assert state["can_redo"] is True

    def test_notification_get_set(self, review: ReviewState, state: ReactiveDict) -> None:
        assert review.notification == ""
        review.notification = "Saved"
        assert review.notification == "Saved"
        assert state["notification"] == "Saved"


# ---------------------------------------------------------------------------
# ReviewState — grading inputs
# ---------------------------------------------------------------------------


class TestReviewStateGradingInputs:
    """set_grading_input and clear_grading_inputs."""

    @pytest.fixture
    def review(self) -> ReviewState:
        return ReviewState(create_default_state())

    def test_set_grading_input(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 3.5)
        assert review.grading_inputs["code_quality_design"] == 3.5

    def test_set_multiple_dimensions(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 4.0)
        review.set_grading_input("creativity", 2.0)
        assert review.grading_inputs["code_quality_design"] == 4.0
        assert review.grading_inputs["creativity"] == 2.0

    def test_clear_grading_inputs(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 4.0)
        review.clear_grading_inputs()
        for key in [
            "code_quality_design",
            "code_execution_results",
            "assignment_requirements",
            "scientific_programming",
            "creativity",
        ]:
            assert review.grading_inputs.get(key) == 0.0

    def test_set_grading_input_pushes_undo(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 3.0)
        assert review.can_undo is True

    def test_clear_grading_inputs_pushes_undo(self, review: ReviewState) -> None:
        review.clear_grading_inputs()
        assert review.can_undo is True
        assert review.can_redo is False


# ---------------------------------------------------------------------------
# ReviewState — checkbox toggling
# ---------------------------------------------------------------------------


class TestReviewStateCheckboxToggling:
    """toggle_checkbox and set_comment."""

    @pytest.fixture
    def review(self) -> ReviewState:
        return ReviewState(create_default_state())

    def test_toggle_adds_item(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        cs = review.category_selections["code_quality"]
        assert "code_quality::positive::Clean" in cs.checked_items

    def test_toggle_removes_item(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        cs = review.category_selections["code_quality"]
        assert "code_quality::positive::Clean" not in cs.checked_items

    def test_toggle_creates_category_if_missing(self, review: ReviewState) -> None:
        review.toggle_checkbox("new_cat", "new_cat::neutral::Item")
        assert "new_cat" in review.category_selections
        cs = review.category_selections["new_cat"]
        assert "new_cat::neutral::Item" in cs.checked_items
        assert cs.notes == ""

    def test_toggle_pushes_undo(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        assert review.can_undo is True

    def test_set_comment(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.set_comment("code_quality", "Nice job")
        cs = review.category_selections["code_quality"]
        assert cs.notes == "Nice job"
        assert "code_quality::positive::Clean" in cs.checked_items

    def test_set_comment_creates_category_if_missing(self, review: ReviewState) -> None:
        review.set_comment("new_cat", "Some notes")
        assert "new_cat" in review.category_selections
        cs = review.category_selections["new_cat"]
        assert cs.notes == "Some notes"
        assert cs.checked_items == []

    def test_toggle_multiple_categories(self, review: ReviewState) -> None:
        review.toggle_checkbox("cat_a", "cat_a::positive::A")
        review.toggle_checkbox("cat_b", "cat_b::negative::B")
        assert len(review.category_selections) == 2
        assert "cat_a::positive::A" in review.category_selections["cat_a"].checked_items
        assert "cat_b::negative::B" in review.category_selections["cat_b"].checked_items


# ---------------------------------------------------------------------------
# ReviewState — session conversion
# ---------------------------------------------------------------------------


class TestReviewStateSessionConversion:
    """to_session and load_from_session round-trip."""

    @pytest.fixture
    def review(self) -> ReviewState:
        return ReviewState(create_default_state())

    def test_to_session_empty(self, review: ReviewState) -> None:
        session = review.to_session()
        assert isinstance(session, ReviewSession)
        assert session.student_id == ""
        assert session.assignment_id == ""
        assert session.category_selections == {}
        assert session.grading_inputs == {}
        assert session.generated_text == ""

    def test_to_session_populated(self, review: ReviewState) -> None:
        review.mode = "review"
        review.student_id = "WS2025_42"
        review.assignment_id = "assignment_01"
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.set_grading_input("creativity", 3.0)
        review.generated_text = "Evaluation text"

        session = review.to_session()
        assert session.student_id == "WS2025_42"
        assert session.assignment_id == "assignment_01"
        assert "code_quality" in session.category_selections
        assert session.grading_inputs.get("creativity") == 3.0
        assert session.generated_text == "Evaluation text"
        assert session.metadata.get("mode") == "review"

    def test_load_from_session_round_trip(self, review: ReviewState) -> None:
        review.mode = "review"
        review.student_id = "WS2025_42"
        review.assignment_id = "assignment_01"
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.set_grading_input("creativity", 3.0)
        review.generated_text = "Evaluation text"

        session = review.to_session()

        # Create fresh state and restore
        fresh = ReviewState(create_default_state())
        fresh.load_from_session(session)

        assert fresh.student_id == "WS2025_42"
        assert fresh.assignment_id == "assignment_01"
        assert fresh.generated_text == "Evaluation text"
        assert fresh.mode == "review"
        assert "code_quality" in fresh.category_selections
        assert fresh.grading_inputs.get("creativity") == 3.0
        assert (
            "code_quality::positive::Clean"
            in fresh.category_selections["code_quality"].checked_items
        )


# ---------------------------------------------------------------------------
# Undo / redo
# ---------------------------------------------------------------------------


class TestUndoRedo:
    """Undo and redo operations on ReviewState."""

    @pytest.fixture
    def review(self) -> ReviewState:
        return ReviewState(create_default_state())

    def test_undo_reverts_checkbox_toggle(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        assert (
            "code_quality::positive::Clean"
            in review.category_selections["code_quality"].checked_items
        )

        review.undo()
        cs = review.category_selections.get("code_quality")
        assert cs is None or "code_quality::positive::Clean" not in cs.checked_items

    def test_redo_reapplies_undone_toggle(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.undo()
        review.redo()
        assert (
            "code_quality::positive::Clean"
            in review.category_selections["code_quality"].checked_items
        )

    def test_undo_empty_stack_does_nothing(self, review: ReviewState) -> None:
        review.undo()  # Should not raise
        assert review.category_selections == {}

    def test_redo_empty_stack_does_nothing(self, review: ReviewState) -> None:
        review.redo()  # Should not raise
        assert review.category_selections == {}

    def test_new_action_clears_redo_stack(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.undo()
        assert review.can_redo is True
        review.toggle_checkbox("code_quality", "code_quality::neutral::OK")
        assert review.can_redo is False

    def test_undo_restores_grading_inputs(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 4.0)
        review.set_grading_input("code_quality_design", 5.0)
        review.undo()
        assert review.grading_inputs["code_quality_design"] == 4.0

    def test_redo_restores_grading_inputs(self, review: ReviewState) -> None:
        review.set_grading_input("code_quality_design", 4.0)
        review.set_grading_input("code_quality_design", 5.0)
        review.undo()
        review.redo()
        assert review.grading_inputs["code_quality_design"] == 5.0

    def test_clear_history(self, review: ReviewState) -> None:
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean2")
        review.clear_history()
        assert review.can_undo is False
        assert review.can_redo is False
        review.undo()  # Should not raise
        assert (
            "code_quality::positive::Clean2"
            in review.category_selections["code_quality"].checked_items
        )

    def test_can_undo_can_redo_flags(self, review: ReviewState) -> None:
        assert review.can_undo is False
        assert review.can_redo is False

        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        assert review.can_undo is True
        assert review.can_redo is False

        review.undo()
        assert review.can_undo is False
        assert review.can_redo is True

        review.redo()
        assert review.can_undo is True
        assert review.can_redo is False

    def test_max_undo_limit(self, review: ReviewState) -> None:
        """When 50+ snapshots, oldest is evicted."""
        for i in range(55):
            review.toggle_checkbox("code_quality", f"code_quality::positive::Item{i}")

        # We can undo at most 50 times (the first 5 were evicted)
        count = 0
        while review.can_undo:
            review.undo()
            count += 1
        assert count == 50

    def test_undo_preserves_unrelated_state(self, review: ReviewState) -> None:
        review.student_id = "WS2025_42"
        review.toggle_checkbox("code_quality", "code_quality::positive::Clean")
        review.undo()
        # student_id is NOT part of undo snapshot — it persists through undo/redo
        assert review.student_id == "WS2025_42"


# ---------------------------------------------------------------------------
# session_to_dict / dict_to_session
# ---------------------------------------------------------------------------


class TestSerializationHelpers:
    """Stand-alone serialization round-trip helpers."""

    def test_session_to_dict_empty(self) -> None:
        session = ReviewSession()
        result = session_to_dict(session)
        assert result["student_id"] == ""
        assert result["category_selections"] == {}
        assert result["grading_inputs"] == {}

    def test_session_to_dict_populated(self) -> None:
        session = ReviewSession(
            student_id="WS2025_42",
            assignment_id="assignment_01",
            category_selections={
                "code_quality": CategorySelections(
                    checked_items=["code_quality::positive::Clean"],
                    notes="Good",
                ),
            },
            grading_inputs={"creativity": 3.0},
            generated_text="Text",
            metadata={"mode": "review"},
        )
        result = session_to_dict(session)
        assert result["student_id"] == "WS2025_42"
        assert result["category_selections"]["code_quality"]["checked_items"] == [
            "code_quality::positive::Clean"
        ]
        assert result["category_selections"]["code_quality"]["notes"] == "Good"
        assert result["grading_inputs"]["creativity"] == 3.0

    def test_dict_to_session_empty(self) -> None:
        session = dict_to_session({})
        assert isinstance(session, ReviewSession)
        assert session.student_id == ""

    def test_dict_to_session_populated(self) -> None:
        data = {
            "student_id": "WS2025_42",
            "assignment_id": "assignment_01",
            "category_selections": {
                "code_quality": {
                    "checked_items": ["code_quality::positive::Clean"],
                    "notes": "Good",
                },
            },
            "grading_inputs": {"creativity": 3.0},
            "generated_text": "Text",
            "metadata": {"mode": "review"},
        }
        session = dict_to_session(data)
        assert session.student_id == "WS2025_42"
        assert session.category_selections["code_quality"].checked_items == [
            "code_quality::positive::Clean"
        ]
        assert session.category_selections["code_quality"].notes == "Good"
        assert session.grading_inputs["creativity"] == 3.0

    def test_round_trip_full(self) -> None:
        """session_to_dict then dict_to_session preserves all data."""
        original = ReviewSession(
            student_id="WS2025_42",
            assignment_id="assignment_01",
            category_selections={
                "code_quality": CategorySelections(
                    checked_items=[
                        "code_quality::positive::Clean",
                        "code_quality::negative::Messy",
                    ],
                    notes="Mixed",
                ),
            },
            grading_inputs={"creativity": 3.0, "code_quality_design": 4.0},
            generated_text="Generated text content",
            metadata={"mode": "review", "version": "2"},
        )
        restored = dict_to_session(session_to_dict(original))
        assert restored.student_id == original.student_id
        assert restored.assignment_id == original.assignment_id
        assert restored.generated_text == original.generated_text
        assert restored.grading_inputs == original.grading_inputs
        assert restored.metadata == original.metadata
        assert (
            restored.category_selections["code_quality"].checked_items
            == original.category_selections["code_quality"].checked_items
        )
        assert (
            restored.category_selections["code_quality"].notes
            == original.category_selections["code_quality"].notes
        )

    def test_missing_keys_default_to_empty(self) -> None:
        """dict_to_session handles partial dicts gracefully."""
        data = {"student_id": "WS2025_42"}
        session = dict_to_session(data)
        assert session.student_id == "WS2025_42"
        assert session.assignment_id == ""
        assert session.category_selections == {}
        assert session.grading_inputs == {}
        assert session.generated_text == ""
        assert session.metadata == {}
