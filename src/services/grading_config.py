"""Grading configuration — single source of truth for all grading dimensions.

Weights are chosen so that max scores yield exactly 100%:
    6x4 + 6x4 + 6x4 + 6x4 + 4x1 = 24+24+24+24+4 = 100

This matches the old_review_app calculation (table.js):
    weightedSum = Sigma(value x factor)
    where factor = weight, and the sum IS the percentage directly.
"""

from __future__ import annotations

from src.models.grading import GradeDimension, GradingConfig, GradingInputs

# Total raw weight sum across all dimensions (used for percentage scaling).
_TOTAL_WEIGHT: int = 17

# Ordered list of grading dimensions with weights, max points, and display metadata.
# Weights are chosen so that Sigma(max_points x weight) = 100.
_DIMENSIONS: list[GradeDimension] = [
    GradeDimension(
        name="code_quality_design",
        max_points=6,
        weight=4,
    ),
    GradeDimension(
        name="code_execution_results",
        max_points=6,
        weight=4,
    ),
    GradeDimension(
        name="assignment_requirements",
        max_points=6,
        weight=4,
    ),
    GradeDimension(
        name="scientific_programming",
        max_points=6,
        weight=4,
    ),
    GradeDimension(
        name="creativity",
        max_points=4,
        weight=1,
    ),
]

"""Pre-built GradingConfig. Pass to the grade calculator."""
DEFAULT_GRADING_CONFIG: GradingConfig = GradingConfig(dimensions=_DIMENSIONS)


def default_grading_inputs() -> GradingInputs:
    """Create a fresh set of zeroed grading inputs.

    All dimension scores are initialized to 0. Use this as the starting
    point for a new review session.

    Returns:
        GradingInputs with every dimension set to 0.
    """
    scores: dict[str, float] = {
        "code_quality_design": 0.0,
        "code_execution_results": 0.0,
        "assignment_requirements": 0.0,
        "scientific_programming": 0.0,
        "creativity": 0.0,
    }
    return GradingInputs(scores=scores)


def weight_percentage(dim_name: str, config: GradingConfig) -> float:
    """Calculate the percentage weight of a dimension.

    Args:
        dim_name: Name of the dimension (e.g. \"code_quality_design\").
        config: A GradingConfig instance containing the dimensions.

    Returns:
        Percentage contribution (0-100) of the dimension's weight.

    Raises:
        ValueError: If no dimension with the given name is found.
    """
    for dim in config.dimensions:
        if dim.name == dim_name:
            return (dim.weight / _TOTAL_WEIGHT) * 100.0

    raise ValueError(f'Dimension "{dim_name}" not found in config')
