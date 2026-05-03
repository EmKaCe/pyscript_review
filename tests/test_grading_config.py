"""Tests for grading configuration constants and helpers."""

from __future__ import annotations

import pytest
from src.models.grading import GradingConfig, GradingInputs
from src.services.grading_config import (
    DEFAULT_GRADING_CONFIG,
    default_grading_inputs,
    weight_percentage,
)


class TestDefaultGradingConfig:
    """Tests for the DEFAULT_GRADING_CONFIG constant."""

    def test_has_exactly_five_dimensions(self) -> None:
        """DEFAULT_GRADING_CONFIG must have exactly 5 dimensions."""
        assert isinstance(DEFAULT_GRADING_CONFIG, GradingConfig)
        assert len(DEFAULT_GRADING_CONFIG.dimensions) == 5

    def test_has_expected_dimension_names(self) -> None:
        """Dimension names must match the expected set."""
        names = {d.name for d in DEFAULT_GRADING_CONFIG.dimensions}
        expected = {
            "code_quality_design",
            "code_execution_results",
            "assignment_requirements",
            "scientific_programming",
            "creativity",
        }
        assert names == expected

    def test_max_points_match_svelte_parity(self) -> None:
        """Max points must match the Svelte version exactly."""
        dims = {d.name: d for d in DEFAULT_GRADING_CONFIG.dimensions}
        assert dims["code_quality_design"].max_points == 6
        assert dims["code_execution_results"].max_points == 6
        assert dims["assignment_requirements"].max_points == 6
        assert dims["scientific_programming"].max_points == 6
        assert dims["creativity"].max_points == 4

    def test_weights_match_svelte_parity(self) -> None:
        """Weights must match the Svelte version exactly."""
        dims = {d.name: d for d in DEFAULT_GRADING_CONFIG.dimensions}
        assert dims["code_quality_design"].weight == 4
        assert dims["code_execution_results"].weight == 4
        assert dims["assignment_requirements"].weight == 4
        assert dims["scientific_programming"].weight == 4
        assert dims["creativity"].weight == 1

    def test_total_weight_percentage_is_100(self) -> None:
        """Sum of all weight percentages must equal 100."""
        total = sum(
            weight_percentage(d.name, DEFAULT_GRADING_CONFIG)
            for d in DEFAULT_GRADING_CONFIG.dimensions
        )
        assert round(total, 10) == 100.0

    def test_weight_percentage_for_creativity(self) -> None:
        """Creativity (weight=1, total=17) should be ~5.88%."""
        pct = weight_percentage("creativity", DEFAULT_GRADING_CONFIG)
        assert round(pct, 2) == 5.88

    def test_weight_percentage_for_weight_four(self) -> None:
        """Each weight=4 dimension should be ~23.53%."""
        expected = round((4 / 17) * 100, 2)
        for dim_name in [
            "code_quality_design",
            "code_execution_results",
            "assignment_requirements",
            "scientific_programming",
        ]:
            pct = weight_percentage(dim_name, DEFAULT_GRADING_CONFIG)
            assert round(pct, 2) == expected

    def test_weight_percentage_unknown_dimension_raises(self) -> None:
        """Looking up an unknown dimension must raise ValueError."""
        with pytest.raises(ValueError, match="not found in config"):
            weight_percentage("nonexistent_dim", DEFAULT_GRADING_CONFIG)


class TestDefaultGradingInputs:
    """Tests for the default_grading_inputs function."""

    def test_returns_grading_inputs_instance(self) -> None:
        """Must return a GradingInputs instance."""
        inputs = default_grading_inputs()
        assert isinstance(inputs, GradingInputs)

    def test_has_correct_keys(self) -> None:
        """Scores dict must have exactly the 5 expected keys."""
        inputs = default_grading_inputs()
        assert set(inputs.scores.keys()) == {
            "code_quality_design",
            "code_execution_results",
            "assignment_requirements",
            "scientific_programming",
            "creativity",
        }

    def test_all_scores_are_zero(self) -> None:
        """All dimension scores must be initialized to 0.0."""
        inputs = default_grading_inputs()
        for value in inputs.scores.values():
            assert value == 0.0

    def test_creates_fresh_copy_on_each_call(self) -> None:
        """Each call must return a new independent instance."""
        inputs1 = default_grading_inputs()
        inputs2 = default_grading_inputs()
        assert inputs1 is not inputs2
        assert inputs1.scores is not inputs2.scores
