"""Tests for all data models in src/models/.

Verifies import correctness, Pydantic model creation/serialization,
grade boundary correctness, and Field(description=...) compliance.
"""

from __future__ import annotations

from pydantic import BaseModel
from src.models import (
    GERMAN_GRADE_BOUNDARIES,
    AssignmentConfig,
    Category,
    CategorySelections,
    CriteriaBundle,
    CurrentSessionRecord,
    DbExport,
    GradeBoundary,
    GradeDimension,
    GradeResult,
    GradingConfig,
    GradingInputs,
    MainPoint,
    PerDimensionResult,
    ReviewRecord,
    ReviewSession,
    Sentiment,
    SubPoint,
)


def test_all_imports_resolve() -> None:
    """Verify every model class can be imported without error."""
    # Criteria models
    assert Sentiment.POSITIVE.value == "positive"
    assert Sentiment.NEGATIVE.value == "negative"
    assert Sentiment.NEUTRAL.value == "neutral"
    assert issubclass(SubPoint, BaseModel)
    assert issubclass(MainPoint, BaseModel)
    assert issubclass(Category, BaseModel)
    assert issubclass(CriteriaBundle, BaseModel)
    assert issubclass(AssignmentConfig, BaseModel)

    # Session models (dataclasses)
    assert CategorySelections is not None
    assert ReviewSession is not None

    # Grading models (dataclasses)
    assert GradeBoundary is not None
    assert GradeDimension is not None
    assert GradingConfig is not None
    assert GradingInputs is not None
    assert GradeResult is not None
    assert PerDimensionResult is not None

    # DB models (dataclasses)
    assert ReviewRecord is not None
    assert CurrentSessionRecord is not None
    assert DbExport is not None


def test_german_grade_boundaries_count() -> None:
    """GERMAN_GRADE_BOUNDARIES has exactly 11 entries."""
    assert len(GERMAN_GRADE_BOUNDARIES) == 11


def test_german_grade_boundaries_values() -> None:
    """Verify all 11 boundaries have correct values and ordering."""
    expected = [
        (95.0, 1.0),
        (90.0, 1.3),
        (85.0, 1.7),
        (80.0, 2.0),
        (75.0, 2.3),
        (70.0, 2.7),
        (65.0, 3.0),
        (60.0, 3.3),
        (55.0, 3.7),
        (50.0, 4.0),
        (0.0, 5.0),
    ]
    for boundary, (expected_pct, expected_grade) in zip(
        GERMAN_GRADE_BOUNDARIES, expected, strict=False
    ):
        assert boundary.min_percentage == expected_pct
        assert boundary.grade == expected_grade


def test_german_grade_boundaries_descending() -> None:
    """Boundaries are sorted descending by min_percentage."""
    for i in range(len(GERMAN_GRADE_BOUNDARIES) - 1):
        assert (
            GERMAN_GRADE_BOUNDARIES[i].min_percentage
            >= GERMAN_GRADE_BOUNDARIES[i + 1].min_percentage
        )


def test_sub_point_creation() -> None:
    """SubPoint can be created with text and optional id."""
    sp = SubPoint(text="Good variable naming", id="var_naming_01")
    assert sp.text == "Good variable naming"
    assert sp.id == "var_naming_01"


def test_sub_point_default_id() -> None:
    """SubPoint id defaults to None."""
    sp = SubPoint(text="Good variable naming")
    assert sp.text == "Good variable naming"
    assert sp.id is None


def test_main_point_creation() -> None:
    """MainPoint can be created with text, sentiment, and sub_points."""
    sp = SubPoint(text="Uses meaningful names")
    mp = MainPoint(
        text="Naming Conventions",
        sentiment=Sentiment.POSITIVE,
        sub_points=[sp],
    )
    assert mp.text == "Naming Conventions"
    assert mp.sentiment == Sentiment.POSITIVE
    assert len(mp.sub_points) == 1
    assert mp.sub_points[0].text == "Uses meaningful names"


def test_main_point_default_sub_points() -> None:
    """MainPoint sub_points defaults to empty list (no mutable default issue)."""
    mp1 = MainPoint(text="Naming", sentiment=Sentiment.POSITIVE)
    mp2 = MainPoint(text="Structure", sentiment=Sentiment.NEUTRAL)
    assert len(mp1.sub_points) == 0
    assert len(mp2.sub_points) == 0
    # Ensure no shared mutable default
    assert mp1.sub_points is not mp2.sub_points


def test_category_creation() -> None:
    """Category can be created with name, slug, weight, and main_points."""
    mp = MainPoint(text="Code Quality", sentiment=Sentiment.POSITIVE)
    cat = Category(
        name="Code Quality & Design",
        slug="code_quality_design",
        weight=4,
        main_points=[mp],
    )
    assert cat.name == "Code Quality & Design"
    assert cat.slug == "code_quality_design"
    assert cat.weight == 4
    assert len(cat.main_points) == 1


def test_criteria_bundle_creation() -> None:
    """CriteriaBundle can be created with assignment info and categories."""
    cat = Category(
        name="Code Quality",
        slug="code_quality",
        weight=4,
        main_points=[MainPoint(text="Good practices", sentiment=Sentiment.POSITIVE)],
    )
    bundle = CriteriaBundle(
        assignment_id="hw01",
        assignment_name="Homework 1",
        categories=[cat],
    )
    assert bundle.assignment_id == "hw01"
    assert bundle.assignment_name == "Homework 1"
    assert len(bundle.categories) == 1


def test_criteria_bundle_serialization() -> None:
    """CriteriaBundle can be serialized to dict and back."""
    cat = Category(
        name="Testing",
        slug="testing",
        weight=4,
        main_points=[MainPoint(text="Tests present", sentiment=Sentiment.POSITIVE)],
    )
    bundle = CriteriaBundle(
        assignment_id="hw02",
        assignment_name="Homework 2",
        categories=[cat],
    )
    data = bundle.model_dump(mode="json")
    restored = CriteriaBundle.model_validate(data)
    assert restored.assignment_id == "hw02"
    assert restored.categories[0].name == "Testing"


def test_assignment_config_defaults() -> None:
    """AssignmentConfig has sensible defaults for enabled and max_points."""
    config = AssignmentConfig(
        id="hw01",
        name="Homework 1",
        criteria_file="criteria/hw01.yaml",
    )
    assert config.enabled is True
    assert config.max_points == 24


def test_assignment_config_override() -> None:
    """AssignmentConfig defaults can be overridden."""
    config = AssignmentConfig(
        id="hw02",
        name="Homework 2",
        criteria_file="criteria/hw02.yaml",
        enabled=False,
        max_points=30,
    )
    assert config.enabled is False
    assert config.max_points == 30


def test_category_selections() -> None:
    """CategorySelections dataclass stores checked items and notes."""
    sel = CategorySelections(
        checked_items=["point_01", "point_02"],
        notes="Good work overall",
    )
    assert sel.checked_items == ["point_01", "point_02"]
    assert sel.notes == "Good work overall"


def test_category_selections_defaults() -> None:
    """CategorySelections defaults are empty list and empty string."""
    sel = CategorySelections()
    assert sel.checked_items == []
    assert sel.notes == ""


def test_review_session_defaults() -> None:
    """ReviewSession has safe defaults for all fields."""
    session = ReviewSession()
    assert session.student_id == ""
    assert session.assignment_id == ""
    assert session.category_selections == {}
    assert session.grading_inputs == {}
    assert session.generated_text == ""
    assert session.metadata == {}


def test_review_session_creation() -> None:
    """ReviewSession can be created with full data."""
    session = ReviewSession(
        student_id="2026SS_42",
        assignment_id="hw01",
        category_selections={
            "code_quality": CategorySelections(
                checked_items=["good_names"],
                notes="Nice naming",
            ),
        },
        grading_inputs={"code_quality_design": 5.0},
        generated_text="Good submission.",
        metadata={"mode": "teacher"},
    )
    assert session.student_id == "2026SS_42"
    assert session.grading_inputs["code_quality_design"] == 5.0
    assert session.metadata["mode"] == "teacher"


def test_grade_boundary_dataclass() -> None:
    """GradeBoundary stores min_percentage and grade."""
    gb = GradeBoundary(min_percentage=80.0, grade=2.0)
    assert gb.min_percentage == 80.0
    assert gb.grade == 2.0


def test_grade_dimension() -> None:
    """GradeDimension stores name, max_points, and weight."""
    dim = GradeDimension(name="Code Quality", max_points=6, weight=4)
    assert dim.name == "Code Quality"
    assert dim.max_points == 6
    assert dim.weight == 4


def test_grading_config() -> None:
    """GradingConfig holds a list of GradeDimension."""
    dims = [
        GradeDimension(name="Code Quality", max_points=6, weight=4),
        GradeDimension(name="Creativity", max_points=4, weight=1),
    ]
    config = GradingConfig(dimensions=dims)
    assert len(config.dimensions) == 2
    assert config.dimensions[1].name == "Creativity"


def test_grading_inputs() -> None:
    """GradingInputs stores a dict of scores."""
    inputs = GradingInputs(scores={"code_quality": 5.0, "creativity": 3.0})
    assert inputs.scores["code_quality"] == 5.0
    assert inputs.scores["creativity"] == 3.0


def test_per_dimension_result() -> None:
    """PerDimensionResult stores breakdown for a single dimension."""
    pdr = PerDimensionResult(
        name="Code Quality",
        score=5.0,
        max_points=6,
        weight=4,
        weighted_score=20.0,
        percentage=83.33,
    )
    assert pdr.name == "Code Quality"
    assert pdr.weighted_score == 20.0
    assert pdr.percentage == 83.33


def test_grade_result() -> None:
    """GradeResult stores overall grade with per-dimension breakdown."""
    pdr = PerDimensionResult(
        name="Code Quality",
        score=5.0,
        max_points=6,
        weight=4,
        weighted_score=20.0,
        percentage=83.33,
    )
    result = GradeResult(
        percentage=83.33,
        grade=2.0,
        near_fence=False,
        per_dimension=[pdr],
    )
    assert result.percentage == 83.33
    assert result.grade == 2.0
    assert result.near_fence is False
    assert len(result.per_dimension) == 1


def test_grade_result_near_fence() -> None:
    """GradeResult near_fence can be True."""
    result = GradeResult(
        percentage=78.5,
        grade=2.3,
        near_fence=True,
        per_dimension=[],
    )
    assert result.near_fence is True


def test_review_record() -> None:
    """ReviewRecord stores all persisted review fields."""
    record = ReviewRecord(
        id="rec_001",
        student_id="2026SS_42",
        assignment_id="hw01",
        semester="2026SS",
        category_selections={"cat1": {"checked": ["a"]}},
        grading_inputs={"dim1": 5.0},
        grade_result={"percentage": 83.33, "grade": 2.0},
        generated_text="Good work.",
        created_at="2026-01-15T10:00:00Z",
        updated_at="2026-01-15T12:00:00Z",
    )
    assert record.id == "rec_001"
    assert record.semester == "2026SS"
    assert record.grade_result["grade"] == 2.0


def test_current_session_record() -> None:
    """CurrentSessionRecord uses __current__ sentinel and stores data dict."""
    sess = CurrentSessionRecord(
        data={"student_id": "2026SS_42", "assignment_id": "hw01"},
    )
    assert sess.id == "__current__"
    assert sess.data["student_id"] == "2026SS_42"


def test_db_export() -> None:
    """DbExport wraps version, timestamp, and list of reviews."""
    record = ReviewRecord(
        id="rec_001",
        student_id="2026SS_42",
        assignment_id="hw01",
        semester="2026SS",
        category_selections={},
        grading_inputs={},
        grade_result={},
        generated_text="",
        created_at="2026-01-15T10:00:00Z",
        updated_at="2026-01-15T12:00:00Z",
    )
    export = DbExport(
        version=1,
        exported_at="2026-01-15T12:00:00Z",
        reviews=[record],
    )
    assert export.version == 1
    assert len(export.reviews) == 1


def test_pydantic_field_descriptions_present() -> None:
    """Every Pydantic model field has a Field(description=...).

    This ensures the Field(description=...) convention is followed
    for all Pydantic models in criteria.py.
    """
    pydantic_models = [
        SubPoint,
        MainPoint,
        Category,
        CriteriaBundle,
        AssignmentConfig,
    ]
    for model_cls in pydantic_models:
        for field_name, field_info in model_cls.model_fields.items():
            assert field_info.description, (
                f"{model_cls.__name__}.{field_name} is missing Field(description=...)"
            )


def test_grade_boundary_correct_deduction() -> None:
    """Verify 80% maps to 2.0 (B+), 79% maps to 2.3 (B)."""

    def lookup_grade(pct: float) -> float:
        for boundary in GERMAN_GRADE_BOUNDARIES:
            if pct >= boundary.min_percentage:
                return boundary.grade
        return 5.0

    assert lookup_grade(80.0) == 2.0
    assert lookup_grade(79.0) == 2.3
    assert lookup_grade(95.0) == 1.0
    assert lookup_grade(94.0) == 1.3
    assert lookup_grade(50.0) == 4.0
    assert lookup_grade(49.0) == 5.0
    assert lookup_grade(100.0) == 1.0
