"""Tests for the text generator service.

Covers:
    - Full evaluation text output format matching Svelte text-generator.ts.
    - All three sentiment sections: positive, neutral, negative.
    - Category grouping and ordering.
    - Empty selections (no categories should appear).
    - Additional notes inclusion/exclusion.
    - Categories with no selections are omitted.
"""

from __future__ import annotations

from src.models.criteria import Category, CriteriaBundle, MainPoint, Sentiment, SubPoint
from src.models.session import CategorySelections, ReviewSession
from src.services.text_generator import generate_evaluation_text


def _make_criteria_bundle(
    categories: list[Category] | None = None,
) -> CriteriaBundle:
    """Create a minimal CriteriaBundle for testing.

    Args:
        categories: Optional list of categories (defaults to three categories).

    Returns:
        A CriteriaBundle instance.
    """
    if categories is not None:
        return CriteriaBundle(
            assignment_id="assignment_01",
            assignment_name="Test Assignment",
            categories=categories,
        )
    return CriteriaBundle(
        assignment_id="assignment_01",
        assignment_name="Test Assignment",
        categories=[
            Category(
                name="Code Quality",
                slug="code_quality",
                weight=4,
                main_points=[
                    MainPoint(
                        text="Good practices",
                        sentiment=Sentiment.POSITIVE,
                        sub_points=[
                            SubPoint(text="Clean variable naming"),
                            SubPoint(text="Proper function structure"),
                        ],
                    ),
                    MainPoint(
                        text="Minor issues",
                        sentiment=Sentiment.NEGATIVE,
                        sub_points=[
                            SubPoint(text="Missing type hints"),
                            SubPoint(text="Inconsistent indentation"),
                        ],
                    ),
                ],
            ),
            Category(
                name="Documentation",
                slug="documentation",
                weight=3,
                main_points=[
                    MainPoint(
                        text="Docs quality",
                        sentiment=Sentiment.NEUTRAL,
                        sub_points=[
                            SubPoint(text="Docstrings are adequate"),
                            SubPoint(text="Comments explain intent"),
                        ],
                    ),
                ],
            ),
            Category(
                name="Creativity",
                slug="creativity",
                weight=1,
                main_points=[
                    MainPoint(
                        text="Innovation",
                        sentiment=Sentiment.POSITIVE,
                        sub_points=[
                            SubPoint(text="Novel approach to problem"),
                            SubPoint(text="Elegant algorithm choice"),
                        ],
                    ),
                ],
            ),
        ],
    )


def _make_session(
    student_id: str = "2026SS_42",
    assignment_id: str = "assignment_01",
    category_selections: dict[str, CategorySelections] | None = None,
) -> ReviewSession:
    """Create a ReviewSession with defaults.

    Args:
        student_id: Student identifier.
        assignment_id: Assignment identifier.
        category_selections: Per-category selections.

    Returns:
        A ReviewSession instance.
    """
    if category_selections is None:
        category_selections = {}
    return ReviewSession(
        student_id=student_id,
        assignment_id=assignment_id,
        category_selections=category_selections,
    )


# ---------------------------------------------------------------------------
# Output format structure
# ---------------------------------------------------------------------------


class TestOutputFormat:
    """Tests for the overall output format structure."""

    def test_header_format(self) -> None:
        """Header should be 'Evaluation for {student_id} — {assignment_id}'."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(
            student_id="2026SS_42",
            assignment_id="assignment_01",
            category_selections=selections,
        )
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        assert lines[0] == "Evaluation for 2026SS_42 \u2014 assignment_01"
        assert lines[1] == "=" * 50
        assert lines[2] == ""

    def test_positive_section_heading(self) -> None:
        """Positive selections produce '## Positive Observations'."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Positive Observations" in result

    def test_neutral_section_heading(self) -> None:
        """Neutral selections produce '## General Observations'."""
        selections = {
            "documentation": CategorySelections(
                checked_items=["documentation::neutral::Docstrings are adequate"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## General Observations" in result

    def test_negative_section_heading(self) -> None:
        """Negative selections produce '## Areas for Improvement'."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::negative::Missing type hints"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Areas for Improvement" in result

    def test_bullet_format(self) -> None:
        """Bullet items should be indented with '  • '."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        bullet_lines = [line for line in lines if line.startswith("  \u2022 ")]
        assert len(bullet_lines) >= 1
        assert "Clean variable naming" in bullet_lines[0]

    def test_category_name_format(self) -> None:
        """Category names should be bold: '**{category_name}**'."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "**Code Quality**" in result


# ---------------------------------------------------------------------------
# Sentiment grouping
# ---------------------------------------------------------------------------


class TestSentimentGrouping:
    """Tests for correct sentiment-based grouping."""

    def test_positive_goes_to_positive_section(self) -> None:
        """Positive items should appear under Positive Observations."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        positive_idx = result.index("## Positive Observations")
        has_negative = "## Areas for Improvement" in result
        has_neutral = "## General Observations" in result
        # Clean variable naming should be in the positive section.
        assert result.index("Clean variable naming") > positive_idx
        assert not has_negative
        assert not has_neutral

    def test_negative_goes_to_negative_section(self) -> None:
        """Negative items should appear under Areas for Improvement."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::negative::Missing type hints"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        neg_idx = result.index("## Areas for Improvement")
        assert result.index("Missing type hints") > neg_idx

    def test_neutral_goes_to_neutral_section(self) -> None:
        """Neutral items should appear under General Observations."""
        selections = {
            "documentation": CategorySelections(
                checked_items=["documentation::neutral::Docstrings are adequate"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        neutral_idx = result.index("## General Observations")
        assert result.index("Docstrings are adequate") > neutral_idx


# ---------------------------------------------------------------------------
# Category grouping within sections
# ---------------------------------------------------------------------------


class TestCategoryGrouping:
    """Tests for category grouping within sentiment sections."""

    def test_items_grouped_by_category(self) -> None:
        """Same-category items should be under a single bold heading."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=[
                    "code_quality::positive::Clean variable naming",
                    "code_quality::positive::Proper function structure",
                ],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        # Find the category header and count bullets after it.
        cat_idx = lines.index("**Code Quality**")
        bullets_after = [line for line in lines[cat_idx + 1 :] if line.startswith("  \u2022 ")]
        assert len(bullets_after) == 2

    def test_multiple_categories_in_same_section(self) -> None:
        """Multiple categories in same sentiment should both appear."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
            "creativity": CategorySelections(
                checked_items=["creativity::positive::Novel approach to problem"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        cat_names = ["**Code Quality**", "**Creativity**"]
        for name in cat_names:
            assert name in result

    def test_categories_without_selections_omitted(self) -> None:
        """Categories with no checked items should NOT appear."""
        # Only check creativity, not code_quality.
        selections = {
            "creativity": CategorySelections(
                checked_items=["creativity::positive::Novel approach to problem"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "**Code Quality**" not in result


# ---------------------------------------------------------------------------
# Additional notes
# ---------------------------------------------------------------------------


class TestAdditionalNotes:
    """Tests for the Additional Notes section."""

    def test_notes_section_included_when_present(self) -> None:
        """Additional Notes section should appear when there are non-empty notes."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
                notes="Student showed great improvement.",
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Additional Notes" in result
        assert "**Code Quality**: Student showed great improvement." in result

    def test_notes_section_omitted_when_empty(self) -> None:
        """Additional Notes section should NOT appear when all notes are empty."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
                notes="",
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Additional Notes" not in result

    def test_notes_section_omitted_when_whitespace_only(self) -> None:
        """Notes with only whitespace should be treated as empty."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
                notes="   ",
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Additional Notes" not in result

    def test_multiple_notes(self) -> None:
        """Multiple categories with notes should all appear."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
                notes="Good structure.",
            ),
            "documentation": CategorySelections(
                checked_items=["documentation::neutral::Docstrings are adequate"],
                notes="Could improve API docs.",
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "**Code Quality**: Good structure." in result
        assert "**Documentation**: Could improve API docs." in result


# ---------------------------------------------------------------------------
# Edge cases and empty states
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and empty states."""

    def test_no_selections_returns_only_header(self) -> None:
        """Empty selections should produce only header and separator."""
        session = _make_session(category_selections={})
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        assert lines[0].startswith("Evaluation for")
        assert lines[1] == "=" * 50
        assert len(lines) == 3  # Header, separator, blank line — nothing else.

    def test_unknown_category_slug_ignored(self) -> None:
        """Unknown category slugs that don't match criteria should be ignored."""
        selections = {
            "nonexistent_category": CategorySelections(
                checked_items=["nonexistent::positive::Something"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        assert len(lines) == 3  # Only header/separator/blank.

    def test_unmatched_key_format_ignored(self) -> None:
        """Keys that don't match any sub-point should be ignored."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Non-existent subpoint"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        lines = result.split("\n")
        assert len(lines) == 3  # Only header/separator/blank.

    def test_full_output_trailing_newline_not_required(self) -> None:
        """Output should not end with a blank line (no trailing newline)."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert result != ""
        # Last character should not be a blank line.
        assert not result.endswith("\n\n")

    def test_output_contains_category_content(self) -> None:
        """Output should contain the expected category content."""
        selections = {
            "code_quality": CategorySelections(
                checked_items=["code_quality::positive::Clean variable naming"],
            ),
        }
        session = _make_session(category_selections=selections)
        criteria = _make_criteria_bundle()
        result = generate_evaluation_text(session, criteria)
        assert "## Positive Observations" in result
        assert "**Code Quality**" in result
        assert "Clean variable naming" in result
