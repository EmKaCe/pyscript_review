"""Tests for the grade calculator service.

Covers:
    - All 11 German grade boundaries.
    - Perfect score and zero score.
    - Edge cases near boundary thresholds (50.0, 49.9, 94.9).
    - Near-fence detection.
    - Score clamping (negative and above-max scores).
"""

from __future__ import annotations

from src.models.grading import (
    GERMAN_GRADE_BOUNDARIES,
    GradingInputs,
)
from src.services.grade_calculator import calculate_grade, get_grade_boundary
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


# ---------------------------------------------------------------------------
# get_grade_boundary
# ---------------------------------------------------------------------------


class TestGetGradeBoundary:
    """Tests for get_grade_boundary()."""

    def test_scores_at_or_above_95_return_1_0(self) -> None:
        """95.0 and above should map to grade 1.0."""
        assert get_grade_boundary(95.0).grade == 1.0
        assert get_grade_boundary(100.0).grade == 1.0

    def test_scores_90_94_9_return_1_3(self) -> None:
        """Scores in [90, 95) should map to grade 1.3."""
        assert get_grade_boundary(90.0).grade == 1.3
        assert get_grade_boundary(94.9).grade == 1.3

    def test_scores_85_89_9_return_1_7(self) -> None:
        """Scores in [85, 90) should map to grade 1.7."""
        assert get_grade_boundary(85.0).grade == 1.7
        assert get_grade_boundary(89.9).grade == 1.7

    def test_scores_80_84_9_return_2_0(self) -> None:
        """Scores in [80, 85) should map to grade 2.0."""
        assert get_grade_boundary(80.0).grade == 2.0
        assert get_grade_boundary(84.9).grade == 2.0

    def test_scores_75_79_9_return_2_3(self) -> None:
        """Scores in [75, 80) should map to grade 2.3."""
        assert get_grade_boundary(75.0).grade == 2.3
        assert get_grade_boundary(79.9).grade == 2.3

    def test_scores_70_74_9_return_2_7(self) -> None:
        """Scores in [70, 75) should map to grade 2.7."""
        assert get_grade_boundary(70.0).grade == 2.7
        assert get_grade_boundary(74.9).grade == 2.7

    def test_scores_65_69_9_return_3_0(self) -> None:
        """Scores in [65, 70) should map to grade 3.0."""
        assert get_grade_boundary(65.0).grade == 3.0
        assert get_grade_boundary(69.9).grade == 3.0

    def test_scores_60_64_9_return_3_3(self) -> None:
        """Scores in [60, 65) should map to grade 3.3."""
        assert get_grade_boundary(60.0).grade == 3.3
        assert get_grade_boundary(64.9).grade == 3.3

    def test_scores_55_59_9_return_3_7(self) -> None:
        """Scores in [55, 60) should map to grade 3.7."""
        assert get_grade_boundary(55.0).grade == 3.7
        assert get_grade_boundary(59.9).grade == 3.7

    def test_scores_50_54_9_return_4_0(self) -> None:
        """Scores in [50, 55) should map to grade 4.0."""
        assert get_grade_boundary(50.0).grade == 4.0
        assert get_grade_boundary(54.9).grade == 4.0

    def test_scores_below_50_return_5_0(self) -> None:
        """Scores below 50 should map to grade 5.0."""
        assert get_grade_boundary(49.9).grade == 5.0
        assert get_grade_boundary(0.0).grade == 5.0
        assert get_grade_boundary(-1.0).grade == 5.0

    def test_boundary_count_matches_model(self) -> None:
        """All 11 boundaries should be reachable."""
        assert len(GERMAN_GRADE_BOUNDARIES) == 11
        # Verify every boundary in the model is reachable.
        for b in GERMAN_GRADE_BOUNDARIES:
            assert get_grade_boundary(b.min_percentage).grade == b.grade


# ---------------------------------------------------------------------------
# calculate_grade
# ---------------------------------------------------------------------------


class TestCalculateGrade:
    """Tests for calculate_grade()."""

    def test_zero_scores_returns_5_0(self) -> None:
        """All zeros should yield 0%, grade 5.0, near fence (within 5 pts of 4.0)."""
        inputs = default_grading_inputs()
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 0.0
        assert result.grade == 5.0
        # points_to_next_grade = 50.0 → NOT within 5 → BUT points_above_current_grade = 0.0 ≤ 2 → near_fence True
        assert result.near_fence is True
        assert result.points_to_next_grade == 50.0
        assert result.points_above_current_grade == 0.0

    def test_perfect_scores_returns_1_0(self) -> None:
        """Perfect scores (all max) should yield 100%, grade 1.0, not near fence."""
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
        assert result.grade == 1.0
        assert result.near_fence is False
        assert result.points_to_next_grade is None  # Already at top boundary
        assert result.points_above_current_grade == 5.0  # 100 - 95

    def test_barely_passing_50_percent(self) -> None:
        """Exactly 50% should yield grade 4.0 (sufficient), near fence (≤5 pts from 3.7)."""
        # 50% = total_raw=50, max_raw=100
        # With 5 dims: 4x6max*4weight + 1x4max*1weight = 100 max
        # Need 50% → need total_raw=50
        # Easiest: set each of the 4 main dims to 3.0 (3*4=12 each, 48 total)
        # and creativity to 2.0 (2*1=2) → total=50
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
        # points_to_next_grade = 5.0 → within 5 → near_fence True
        assert result.near_fence is True
        assert result.points_to_next_grade == 5.0
        assert result.points_above_current_grade == 0.0

    def test_just_below_50_returns_5_0(self) -> None:
        """49.9% should yield grade 5.0 (failing)."""
        inputs = _make_inputs(
            {
                "code_quality_design": 3.0,
                "code_execution_results": 3.0,
                "assignment_requirements": 3.0,
                "scientific_programming": 3.0,
                "creativity": 1.9,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 3*4*4 + 1.9*1 = 48 + 1.9 = 49.9
        assert result.percentage == 49.9
        assert result.grade == 5.0
        assert result.near_fence is True  # Within 2 pts of 4.0 boundary

    def test_just_below_95_returns_1_3_with_near_fence(self) -> None:
        """94.9% should yield grade 1.3, near fence to 1.0."""
        inputs = _make_inputs(
            {
                "code_quality_design": 5.7,
                "code_execution_results": 5.7,
                "assignment_requirements": 5.7,
                "scientific_programming": 5.7,
                "creativity": 3.5,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # 5.7*4*4 + 3.5*1 = 91.2 + 3.5 = 94.7 — let me recalculate
        # Actually: 5.7*4 (weighted per dim) = 22.8 per main dim → 22.8*4 = 91.2
        # creativity: 3.5*1 = 3.5
        # total_raw = 94.7, max_raw = 100 → 94.7%
        # That's 94.7% → within 2 pts of 95 → near_fence
        assert result.percentage == 94.7
        assert result.grade == 1.3
        assert result.near_fence is True

    def test_scores_clamped_to_max_points(self) -> None:
        """Scores above max_points should be clamped down."""
        inputs = _make_inputs(
            {
                "code_quality_design": 10.0,  # Above max of 6
                "code_execution_results": 6.0,
                "assignment_requirements": 6.0,
                "scientific_programming": 6.0,
                "creativity": 4.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        # All clamped to max → 100%, grade 1.0
        assert result.percentage == 100.0
        assert result.grade == 1.0

    def test_negative_scores_clamped_to_zero(self) -> None:
        """Negative scores should be clamped to 0."""
        inputs = _make_inputs(
            {
                "code_quality_design": -5.0,
                "code_execution_results": 0.0,
                "assignment_requirements": 0.0,
                "scientific_programming": 0.0,
                "creativity": 0.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert result.percentage == 0.0
        assert result.grade == 5.0

    def test_per_dimension_results_present(self) -> None:
        """Each dimension should have a PerDimensionResult entry."""
        inputs = _make_inputs(
            {
                "code_quality_design": 6.0,
                "code_execution_results": 3.0,
                "assignment_requirements": 0.0,
                "scientific_programming": 6.0,
                "creativity": 0.0,
            }
        )
        result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        assert len(result.per_dimension) == 5
        # Verify specific dimension.
        cqd = next(d for d in result.per_dimension if d.name == "code_quality_design")
        assert cqd.score == 6.0
        assert cqd.max_points == 6
        assert cqd.weight == 4
        assert cqd.weighted_score == 24.0
        assert cqd.percentage == 100.0

    def test_partial_scores_within_band(self) -> None:
        """Mid-range scores should produce correct percentage."""
        # All 3/6 in main dims, 2/4 in creativity
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
        # total_raw = 3*4*4 + 2*1 = 48 + 2 = 50
        # max_raw = 100
        # percentage = 50%
        assert result.percentage == 50.0
        assert result.grade == 4.0

    def test_near_fence_false_for_comfortable_margin(self) -> None:
        """Score at 40% → grade 5.0, points_to_next=10 (>5), points_above=40 (>2)."""
        # 40%: grade 5.0 (lowest boundary at 0%).
        # points_to_next_grade = 50 - 40 = 10 > 5 → not near fence by that rule.
        # points_above_current_grade = 40 - 0 = 40 > 2 → not near fence by that rule either.
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
        # 2.4*4*4 + 1.6*1 = 38.4 + 1.6 = 40.0
        assert result.percentage == 40.0
        assert result.grade == 5.0
        assert result.near_fence is False
        assert result.points_to_next_grade == 10.0
        assert result.points_above_current_grade == 40.0
