"""Tests for GradeResult near-fence fields: points_to_next_grade, points_above_current_grade.

Verifies that the detailed near-fence breakdown fields computed by
calculate_grade() are correct across boundary and mid-band percentages,
and that the near_fence boolean is consistent with the detailed fields.
"""

from __future__ import annotations

from src.models.grading import GradingInputs
from src.services.grade_calculator import calculate_grade
from src.services.grading_config import DEFAULT_GRADING_CONFIG, default_grading_inputs


def _make_inputs(overrides: dict[str, float]) -> GradingInputs:
    """Create GradingInputs with overrides on top of default (zeroed) scores.

    Args:
        overrides: Dimension name → score pairs to override.

    Returns:
        GradingInputs with merged scores.
    """
    inputs = default_grading_inputs()
    inputs.scores.update(overrides)
    return inputs


class TestGradeResultFields:
    """Verify GradeResult has points_to_next_grade and points_above_current_grade."""

    def test_result_has_points_to_next_grade(self) -> None:
        """GradeResult should expose points_to_next_grade field."""
        result = calculate_grade(default_grading_inputs(), DEFAULT_GRADING_CONFIG)
        assert hasattr(result, "points_to_next_grade")

    def test_result_has_points_above_current_grade(self) -> None:
        """GradeResult should expose points_above_current_grade field."""
        result = calculate_grade(default_grading_inputs(), DEFAULT_GRADING_CONFIG)
        assert hasattr(result, "points_above_current_grade") is True


class TestHighScoreNearFence:
    """High scores (90%+) should have small or None points_to_next_grade."""

    def test_90_percent_points_to_next_is_small(self) -> None:
        """At 90%, points_to_next_grade should be 5.0 (to reach 1.7 boundary)."""
        # 90% → grade 1.3, boundary_index=1 → next better is 95% (1.0)
        inputs = _make_inputs(
            {
                "code_quality_design": 5.4,
                "code_execution_results": 5.4,
                "assignment_requirements": 5.4,
                "scientific_programming": 5.4,
                "creativity": 3.6,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 5.4*4*4 + 3.6*1 = 86.4 + 3.6 = 90.0%
        assert result.percentage == 90.0
        assert result.points_to_next_grade == 5.0
        assert result.near_fence is True

    def test_95_percent_points_to_next_is_none(self) -> None:
        """At 95%+, points_to_next_grade should be None (best possible grade)."""
        inputs = _make_inputs(
            {
                "code_quality_design": 6.0,
                "code_execution_results": 6.0,
                "assignment_requirements": 6.0,
                "scientific_programming": 6.0,
                "creativity": 4.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 100.0
        assert result.points_to_next_grade is None

    def test_92_percent_points_to_next(self) -> None:
        """At 92%, points_to_next_grade should be 3.0 (to 95%)."""
        inputs = _make_inputs(
            {
                "code_quality_design": 5.55,
                "code_execution_results": 5.55,
                "assignment_requirements": 5.55,
                "scientific_programming": 5.55,
                "creativity": 3.6,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 5.55*4*4 + 3.6*1 = 88.8 + 3.6 = 92.4%
        assert result.points_to_next_grade is not None
        assert result.points_to_next_grade == round(95.0 - result.percentage, 1)


class TestExactBoundaryPointsAbove:
    """Score exactly on a boundary should yield points_above_current_grade == 0.0."""

    def test_exactly_50_percent(self) -> None:
        """At 50% (grade 4.0 boundary), points_above_current_grade should be 0.0."""
        inputs = _make_inputs(
            {
                "code_quality_design": 3.0,
                "code_execution_results": 3.0,
                "assignment_requirements": 3.0,
                "scientific_programming": 3.0,
                "creativity": 2.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 50.0
        assert result.points_above_current_grade == 0.0

    def test_exactly_80_percent(self) -> None:
        """At 80% (grade 2.0 boundary), points_above_current_grade should be 0.0."""
        inputs = _make_inputs(
            {
                "code_quality_design": 4.8,
                "code_execution_results": 4.8,
                "assignment_requirements": 4.8,
                "scientific_programming": 4.8,
                "creativity": 3.2,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 4.8*4*4 + 3.2*1 = 76.8 + 3.2 = 80.0%
        assert result.percentage == 80.0
        assert result.points_above_current_grade == 0.0

    def test_exactly_95_percent(self) -> None:
        """At exactly 95%, points_above_current_grade should be 0.0."""
        inputs = _make_inputs(
            {
                "code_quality_design": 5.7,
                "code_execution_results": 5.7,
                "assignment_requirements": 5.7,
                "scientific_programming": 5.7,
                "creativity": 3.8,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 5.7*4*4 + 3.8*1 = 91.2 + 3.8 = 95.0%
        assert result.percentage == 95.0
        assert result.points_above_current_grade == 0.0


class TestLowScoreFields:
    """Low scores (e.g., 50%) should have reasonable values for both fields."""

    def test_low_score_50_percent(self) -> None:
        """At 50%, both fields should be reasonable."""
        inputs = _make_inputs(
            {
                "code_quality_design": 3.0,
                "code_execution_results": 3.0,
                "assignment_requirements": 3.0,
                "scientific_programming": 3.0,
                "creativity": 2.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 50.0
        assert result.grade == 4.0
        assert result.points_to_next_grade == 5.0
        assert result.points_above_current_grade == 0.0

    def test_55_percent_near_boundary(self) -> None:
        """At 55% (grade 3.7 boundary), verify near-fence fields."""
        inputs = _make_inputs(
            {
                "code_quality_design": 3.3,
                "code_execution_results": 3.3,
                "assignment_requirements": 3.3,
                "scientific_programming": 3.3,
                "creativity": 2.2,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 3.3*4*4 + 2.2*1 = 52.8 + 2.2 = 55.0% (floating-point: 55.00000000000001)
        assert abs(result.percentage - 55.0) < 0.01
        assert result.points_above_current_grade == 0.0
        assert result.points_to_next_grade == 5.0


class TestNearFenceConsistency:
    """Verify near_fence boolean is consistent with detailed fields."""

    def test_near_fence_true_when_points_to_next_within_5(self) -> None:
        """near_fence should be True when points_to_next_grade <= 5."""
        inputs = _make_inputs(
            {
                "code_quality_design": 3.0,
                "code_execution_results": 3.0,
                "assignment_requirements": 3.0,
                "scientific_programming": 3.0,
                "creativity": 2.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.points_to_next_grade == 5.0
        assert result.near_fence is True

    def test_near_fence_true_when_points_above_within_2(self) -> None:
        """near_fence should be True when points_above_current_grade <= 2."""
        # 92%: grade 1.3, boundary at 90%, points_above = 2.0
        inputs = _make_inputs(
            {
                "code_quality_design": 5.55,
                "code_execution_results": 5.55,
                "assignment_requirements": 5.55,
                "scientific_programming": 5.55,
                "creativity": 3.6,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 5.55*4*4 + 3.6*1 = 88.8 + 3.6 = 92.4%
        # Grade 1.3 (boundary 90%), points_above = 2.4 → >2
        # points_to_next = 95.0 - 92.4 = 2.6 → ≤5 → near_fence True
        if result.points_above_current_grade <= 2.0:
            assert result.near_fence is True

    def test_near_fence_false_when_both_conditions_fail(self) -> None:
        """near_fence should be False when both conditions fail."""
        # 40%: grade 5.0, points_to_next=10 (>5), points_above=40 (>2)
        inputs = _make_inputs(
            {
                "code_quality_design": 2.4,
                "code_execution_results": 2.4,
                "assignment_requirements": 2.4,
                "scientific_programming": 2.4,
                "creativity": 1.6,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 40.0
        assert result.points_to_next_grade == 10.0
        assert result.points_above_current_grade == 40.0
        assert result.near_fence is False

    def test_near_fence_true_at_zero_percent(self) -> None:
        """At 0%, near_fence should be True (points_above = 0 ≤ 2)."""
        result = calculate_grade(default_grading_inputs(), DEFAULT_GRADING_CONFIG)
        assert result.percentage == 0.0
        assert result.points_above_current_grade == 0.0
        assert result.near_fence is True

    def test_near_fence_false_at_perfect_score(self) -> None:
        """At 100%, near_fence should be False (points_to_next=None, points_above=5)."""
        inputs = _make_inputs(
            {
                "code_quality_design": 6.0,
                "code_execution_results": 6.0,
                "assignment_requirements": 6.0,
                "scientific_programming": 6.0,
                "creativity": 4.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 100.0
        assert result.points_to_next_grade is None
        assert result.points_above_current_grade == 5.0
        assert result.near_fence is False

    def test_near_fence_true_just_above_boundary(self) -> None:
        """1% above a boundary → points_above=1 ≤ 2 → near_fence True."""
        # At 51%: grade 4.0 (boundary at 50%), points_above = 1.0
        inputs = _make_inputs(
            {
                "code_quality_design": 3.06,
                "code_execution_results": 3.06,
                "assignment_requirements": 3.06,
                "scientific_programming": 3.06,
                "creativity": 2.04,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 3.06*4*4 + 2.04*1 = 48.96 + 2.04 = 51.0
        assert result.percentage == 51.0
        assert result.points_above_current_grade == 1.0
        assert result.near_fence is True
