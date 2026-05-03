"""Weighted grade calculation matching the Svelte grade-calculator.ts formula.

Exports two functions:
    - get_grade_boundary(): Look up a German grade boundary by percentage.
    - calculate_grade(): Compute a full GradeResult from inputs and config.

Formula (from Svelte):
    weighted_score = score * weight
    total_raw      = Σ(weighted_score)
    max_raw        = Σ(max_points * weight)
    percentage     = (total_raw / max_raw) * 100
"""

from __future__ import annotations

from src.models.grading import (
    GERMAN_GRADE_BOUNDARIES,
    GradeBoundary,
    GradeResult,
    GradingConfig,
    GradingInputs,
    PerDimensionResult,
)


def get_grade_boundary(percentage: float) -> GradeBoundary:
    """Find the German grade boundary for a given percentage.

    Iterates the GERMAN_GRADE_BOUNDARIES list (sorted descending by
    min_percentage) and returns the first boundary whose minimum
    percentage the score meets or exceeds. Falls back to the last
    boundary (5.0 / failing) if no boundary is matched.

    Args:
        percentage: The overall percentage score (0-100).

    Returns:
        The matching GradeBoundary.

    Example:
        >>> get_grade_boundary(95.0)
        GradeBoundary(min_percentage=95.0, grade=1.0)
        >>> get_grade_boundary(49.9)
        GradeBoundary(min_percentage=0.0, grade=5.0)
    """
    for boundary in GERMAN_GRADE_BOUNDARIES:
        if percentage >= boundary.min_percentage:
            return boundary
    return GERMAN_GRADE_BOUNDARIES[-1]


def calculate_grade(
    inputs: GradingInputs,
    config: GradingConfig,
) -> GradeResult:
    """Calculate a weighted German grade using the review-app formula.

    For each dimension:
        1. Clamp the raw score to [0, max_points].
        2. Compute weighted_score = clamped_score * weight.
        3. Compute per-dimension percentage = (score / max_points) * 100.

    The overall percentage is: (Σ(weighted_score) / Σ(max_points * weight)) * 100.
    The grade is then looked up via get_grade_boundary().
    The near_fence flag is True when within 2 percentage points of the
    next (better) boundary.

    Args:
        inputs: Raw grading scores per dimension (via inputs.scores dict).
        config: Grading configuration with ordered dimensions.

    Returns:
        A GradeResult with overall percentage, grade, near_fence flag,
        and per-dimension breakdowns.

    Example:
        >>> inputs = default_grading_inputs()
        >>> result = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
        >>> result.grade
        5.0
    """
    total_raw: float = 0.0
    max_raw: float = 0.0
    per_dimension: list[PerDimensionResult] = []

    for dim in config.dimensions:
        if hasattr(inputs, "scores"):
            raw_score = inputs.scores.get(dim.name, 0.0)
        else:
            raw_score = inputs.get(dim.name, 0.0)

        # Clamp score to [0, max_points].
        clamped_score = max(0.0, min(float(raw_score), float(dim.max_points)))

        weighted_score = clamped_score * dim.weight
        max_contribution = dim.max_points * dim.weight
        dim_percentage = (clamped_score / dim.max_points) * 100.0 if dim.max_points > 0 else 0.0

        total_raw += weighted_score
        max_raw += max_contribution

        per_dimension.append(
            PerDimensionResult(
                name=dim.name,
                score=clamped_score,
                max_points=dim.max_points,
                weight=dim.weight,
                weighted_score=weighted_score,
                percentage=dim_percentage,
            ),
        )

    total_percentage = (total_raw / max_raw) * 100.0 if max_raw > 0 else 0.0

    boundary = get_grade_boundary(total_percentage)

    # Find index of matched boundary to check next better one.
    boundary_index: int = -1
    for i, b in enumerate(GERMAN_GRADE_BOUNDARIES):
        if total_percentage >= b.min_percentage:
            boundary_index = i
            break

    # Points-to-next-grade: gap to the next better boundary (index-1).
    points_to_next_grade: float | None = None
    if boundary_index > 0:
        next_boundary = GERMAN_GRADE_BOUNDARIES[boundary_index - 1]
        points_to_next_grade = round(next_boundary.min_percentage - total_percentage, 1)

    # Points-above-current-grade: how far above the current boundary minimum.
    points_above_current_grade: float = round(total_percentage - boundary.min_percentage, 1)

    # near_fence: within 5 pts of next grade OR within 2 pts above current.
    near_fence: bool = (
        points_to_next_grade is not None and points_to_next_grade <= 5.0
    ) or points_above_current_grade <= 2.0

    # US Equivalent
    us_equiv = "F"
    if boundary.grade <= 1.3:
        us_equiv = "A"
    elif boundary.grade <= 2.3:
        us_equiv = "B"
    elif boundary.grade <= 3.3:
        us_equiv = "C"
    elif boundary.grade <= 4.0:
        us_equiv = "D"

    return GradeResult(
        percentage=total_percentage,
        grade=boundary.grade,
        us_equivalent=us_equiv,
        near_fence=near_fence,
        points_to_next_grade=points_to_next_grade,
        points_above_current_grade=points_above_current_grade,
        per_dimension=per_dimension,
    )
