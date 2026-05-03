"""Dataclasses for grade calculation and German grading scale.

Contains the 11-step German grade boundary table and data models
for grading dimensions, inputs, and results.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GradeBoundary:
    """A single boundary in the German grading scale."""

    min_percentage: float = field(
        metadata={"description": "Minimum percentage required for this grade"},
    )
    grade: float = field(
        metadata={"description": "German grade value (1.0 is best, 5.0 is failing)"},
    )


GERMAN_GRADE_BOUNDARIES: list[GradeBoundary] = [
    GradeBoundary(min_percentage=95.0, grade=1.0),
    GradeBoundary(min_percentage=90.0, grade=1.3),
    GradeBoundary(min_percentage=85.0, grade=1.7),
    GradeBoundary(min_percentage=80.0, grade=2.0),
    GradeBoundary(min_percentage=75.0, grade=2.3),
    GradeBoundary(min_percentage=70.0, grade=2.7),
    GradeBoundary(min_percentage=65.0, grade=3.0),
    GradeBoundary(min_percentage=60.0, grade=3.3),
    GradeBoundary(min_percentage=55.0, grade=3.7),
    GradeBoundary(min_percentage=50.0, grade=4.0),
    GradeBoundary(min_percentage=0.0, grade=5.0),
]
"""11-step German grade boundaries. Sorted descending by min_percentage.

    95+  -> 1.0  (excellent)
    90   -> 1.3  (very good)
    85   -> 1.7  (very good)
    80   -> 2.0  (good)
    75   -> 2.3  (good)
    70   -> 2.7  (good)
    65   -> 3.0  (above average)
    60   -> 3.3  (average)
    55   -> 3.7  (below average)
    50   -> 4.0  (sufficient)
    <50  -> 5.0  (insufficient / fail)
"""


@dataclass
class GradeDimension:
    """A single dimension from the grading configuration."""

    name: str = field(
        metadata={"description": "Human-readable name of the dimension"},
    )
    max_points: int = field(
        metadata={"description": "Maximum raw points attainable"},
    )
    weight: int = field(
        metadata={"description": "Weight applied when computing weighted total"},
    )


@dataclass
class GradingConfig:
    """Full grading configuration with ordered dimensions."""

    dimensions: list[GradeDimension] = field(
        metadata={"description": "Ordered list of grading dimensions"},
    )


@dataclass
class GradingInputs:
    """Raw scores entered by the grader for each dimension."""

    scores: dict[str, float] = field(
        metadata={"description": "Dictionary mapping dimension name to entered score"},
    )


@dataclass
class PerDimensionResult:
    """Breakdown for a single grading dimension."""

    name: str = field(metadata={"description": "Name of the dimension"})
    score: float = field(metadata={"description": "Raw score entered by the grader"})
    max_points: int = field(metadata={"description": "Maximum points for this dimension"})
    weight: int = field(metadata={"description": "Weight of this dimension"})
    weighted_score: float = field(
        metadata={"description": "Weighted contribution to total"},
    )
    percentage: float = field(
        metadata={"description": "Percentage achieved in this dimension"},
    )


@dataclass
class GradeResult:
    """Computed grade breakdown returned by the calculator."""

    percentage: float = field(
        metadata={"description": "Overall percentage (0-100)"},
    )
    grade: float = field(
        metadata={"description": "Final German grade on the 1.0-5.0 scale"},
    )
    near_fence: bool = field(
        metadata={
            "description": (
                "Whether the grade is within 2 percentage points of the next boundary "
                "or within 2 points above the current boundary"
            ),
        },
    )
    per_dimension: list[PerDimensionResult] = field(
        metadata={"description": "List of per-dimension result breakdowns"},
    )
    us_equivalent: str = field(
        default="F",
        metadata={"description": "US grade equivalent (A-F)"},
    )
    points_to_next_grade: float | None = field(
        default=None,
        metadata={
            "description": (
                "Percentage points needed to reach the next better grade boundary, "
                "rounded to 1 decimal. None when at top boundary."
            ),
        },
    )
    points_above_current_grade: float = field(
        default=0.0,
        metadata={
            "description": (
                "Percentage points above the current grade's minimum boundary, rounded to 1 decimal"
            ),
        },
    )
