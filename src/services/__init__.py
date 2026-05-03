"""Services — business logic for grading, YAML loading, and state management."""

from src.services.criteria_loader import (
    get_assignments_from_criteria,
    get_criteria_for_assignment,
    load_all_criteria,
    load_assignments,
    load_criteria_for_assignment,
)
from src.services.grade_calculator import (
    calculate_grade,
    get_grade_boundary,
)
from src.services.grading_config import (
    DEFAULT_GRADING_CONFIG,
    default_grading_inputs,
    weight_percentage,
)
from src.services.text_generator import generate_evaluation_text

__all__ = [
    "DEFAULT_GRADING_CONFIG",
    "calculate_grade",
    "default_grading_inputs",
    "generate_evaluation_text",
    "get_assignments_from_criteria",
    "get_criteria_for_assignment",
    "get_grade_boundary",
    "load_all_criteria",
    "load_assignments",
    "load_criteria_for_assignment",
    "weight_percentage",
]
