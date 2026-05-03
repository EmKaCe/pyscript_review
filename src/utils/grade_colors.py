"""Grade-to-CSS-class mappings for German grading scale (1.0-5.0).

Provides color configurations based on the Svelte version's grade-color
mapping: emerald (excellent 1.0-1.7), blue (good 2.0-2.7), violet
(satisfactory 3.0-3.7), amber (sufficient 4.0), red (fail 5.0).
"""

from typing import TypedDict


class GradeColorConfig(TypedDict):
    """Color configuration for a grade display context.

    Attributes:
        bg_class: CSS class for background color.
        text_class: CSS class for text color.
        border_class: CSS class for border color.
        ring_class: CSS class for ring/focus color.
    """

    bg_class: str
    text_class: str
    border_class: str
    ring_class: str


# Grade color bands with upper bound inclusive
_GRADE_BANDS: list[tuple[float, str]] = [
    (1.75, "emerald"),
    (2.75, "blue"),
    (3.75, "violet"),
    (4.05, "amber"),
    (5.05, "red"),
]


def _get_band(grade: float) -> str:
    """Determine the color band for a given grade.

    Args:
        grade: German grade value (1.0-5.0, lower is better).

    Returns:
        Color name string (emerald, blue, violet, amber, or red).
    """
    for upper, color in _GRADE_BANDS:
        if grade <= upper:
            return color
    return "red"


def get_bar_color(pct: float) -> str:
    """Return a solid Tailwind color class based on percentage.

    Args:
        pct: Percentage (0-100).

    Returns:
        Tailwind background color class (e.g., bg-emerald-500).
    """
    if pct >= 85:  # 1.0 - 1.7
        return "bg-emerald-500"
    if pct >= 70:  # 2.0 - 2.7
        return "bg-blue-500"
    if pct >= 55:  # 3.0 - 3.7
        return "bg-violet-500"
    if pct >= 50:  # 4.0
        return "bg-amber-500"
    return "bg-red-500"


def get_grade_color(grade: float) -> str:
    """Return a CSS class string for a grade badge.

    Args:
        grade: German grade value (1.0-5.0, lower is better).

    Returns:
        Tailwind CSS class string for the grade badge background.
    """
    color = _get_band(grade)
    band_map = {
        "emerald": "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/60 "
        "dark:text-emerald-300 border-emerald-200 dark:border-emerald-800",
        "blue": "bg-blue-100 text-blue-800 dark:bg-blue-900/60 "
        "dark:text-blue-300 border-blue-200 dark:border-blue-800",
        "violet": "bg-violet-100 text-violet-800 dark:bg-violet-900/60 "
        "dark:text-violet-300 border-violet-200 dark:border-violet-800",
        "amber": "bg-amber-100 text-amber-800 dark:bg-amber-900/60 "
        "dark:text-amber-300 border-amber-200 dark:border-amber-800",
        "red": "bg-red-100 text-red-800 dark:bg-red-900/60 "
        "dark:text-red-300 border-red-200 dark:border-red-800",
    }
    return band_map[color]


def sidebar_grade_color_config(grade: float) -> GradeColorConfig:
    """Return color config for sidebar grade badge display.

    Args:
        grade: German grade value (1.0-5.0, lower is better).

    Returns:
        GradeColorConfig with bg, text, border, and ring classes.
    """
    color = _get_band(grade)
    configs = {
        "emerald": GradeColorConfig(
            bg_class="bg-emerald-100 dark:bg-emerald-900/60",
            text_class="text-emerald-800 dark:text-emerald-300",
            border_class="border-emerald-200 dark:border-emerald-800",
            ring_class="ring-emerald-300 dark:ring-emerald-700",
        ),
        "blue": GradeColorConfig(
            bg_class="bg-blue-100 dark:bg-blue-900/60",
            text_class="text-blue-800 dark:text-blue-300",
            border_class="border-blue-200 dark:border-blue-800",
            ring_class="ring-blue-300 dark:ring-blue-700",
        ),
        "violet": GradeColorConfig(
            bg_class="bg-violet-100 dark:bg-violet-900/60",
            text_class="text-violet-800 dark:text-violet-300",
            border_class="border-violet-200 dark:border-violet-800",
            ring_class="ring-violet-300 dark:ring-violet-700",
        ),
        "amber": GradeColorConfig(
            bg_class="bg-amber-100 dark:bg-amber-900/60",
            text_class="text-amber-800 dark:text-amber-300",
            border_class="border-amber-200 dark:border-amber-800",
            ring_class="ring-amber-300 dark:ring-amber-700",
        ),
        "red": GradeColorConfig(
            bg_class="bg-red-100 dark:bg-red-900/60",
            text_class="text-red-800 dark:text-red-300",
            border_class="border-red-200 dark:border-red-800",
            ring_class="ring-red-300 dark:ring-red-700",
        ),
    }
    return configs[color]


def card_grade_color_config(grade: float) -> GradeColorConfig:
    """Return color config for review card grade display.

    Uses more subdued colors (no background, text-only variants) suitable
    for embedding in cards without a dedicated badge.

    Args:
        grade: German grade value (1.0-5.0, lower is better).

    Returns:
        GradeColorConfig with bg, text, border, and ring classes.
    """
    color = _get_band(grade)
    configs = {
        "emerald": GradeColorConfig(
            bg_class="bg-green-50 dark:bg-green-950/30",
            text_class="text-green-600 dark:text-green-400",
            border_class="border-green-300 dark:border-green-700",
            ring_class="ring-green-400 dark:ring-green-600",
        ),
        "blue": GradeColorConfig(
            bg_class="bg-blue-50 dark:bg-blue-950/30",
            text_class="text-blue-600 dark:text-blue-400",
            border_class="border-blue-300 dark:border-blue-700",
            ring_class="ring-blue-400 dark:ring-blue-600",
        ),
        "violet": GradeColorConfig(
            bg_class="bg-violet-50 dark:bg-violet-950/30",
            text_class="text-violet-600 dark:text-violet-400",
            border_class="border-violet-300 dark:border-violet-700",
            ring_class="ring-violet-400 dark:ring-violet-600",
        ),
        "amber": GradeColorConfig(
            bg_class="bg-yellow-50 dark:bg-yellow-950/30",
            text_class="text-yellow-600 dark:text-yellow-400",
            border_class="border-yellow-300 dark:border-yellow-700",
            ring_class="ring-yellow-400 dark:ring-yellow-600",
        ),
        "red": GradeColorConfig(
            bg_class="bg-red-50 dark:bg-red-950/30",
            text_class="text-red-600 dark:text-red-400",
            border_class="border-red-300 dark:border-red-700",
            ring_class="ring-red-400 dark:ring-red-600",
        ),
    }
    return configs[color]
