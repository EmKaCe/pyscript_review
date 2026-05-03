"""Tests for ReviewState.get_category_progress().

Covers: no criteria bundle, empty bundle, partial selections, full selections.
"""

from __future__ import annotations

from puepy.reactivity import ReactiveDict
from src.models.criteria import Category, CriteriaBundle, MainPoint
from src.models.session import CategorySelections
from src.state import DEFAULT_STATE, ReviewState


def _make_review_state(**overrides: object) -> ReviewState:
    """Create a ReviewState backed by a fresh ReactiveDict.

    Args:
        overrides: Key-value pairs to override in the ReactiveDict.

    Returns:
        ReviewState wrapping the configured ReactiveDict.
    """
    d = dict(DEFAULT_STATE)
    d.update(overrides)
    return ReviewState(ReactiveDict(d))


def _make_bundle(n_categories: int) -> CriteriaBundle:
    """Build a CriteriaBundle with the given number of empty categories.

    Args:
        n_categories: Number of categories to include.

    Returns:
        CriteriaBundle with n_categories, each having one placeholder main point.
    """
    categories = [
        Category(
            name=f"Category {i}",
            slug=f"cat_{i}",
            weight=1,
            main_points=[MainPoint(text="Point", sentiment="positive")],
        )
        for i in range(n_categories)
    ]
    return CriteriaBundle(
        assignment_id="test",
        assignment_name="Test Assignment",
        categories=categories,
    )


class TestGetCategoryProgressNoBundle:
    """get_category_progress() when no criteria_bundle is set."""

    def test_returns_zeros_when_no_bundle(self) -> None:
        """With criteria_bundle=None, filled and total should both be 0."""
        rs = _make_review_state()
        progress = rs.category_progress
        assert progress == {"filled": 0, "total": 0}

    def test_total_is_zero_when_no_bundle(self) -> None:
        """Total should be 0 (no categories to count)."""
        rs = _make_review_state()
        assert rs.category_progress["total"] == 0


class TestGetCategoryProgressEmptyBundle:
    """get_category_progress() with an empty criteria_bundle (0 categories)."""

    def test_returns_zeros_for_empty_bundle(self) -> None:
        """Bundle with no categories → filled=0, total=0."""
        bundle = CriteriaBundle(
            assignment_id="test",
            assignment_name="Empty",
            categories=[],
        )
        rs = _make_review_state(criteria_bundle=bundle)
        progress = rs.category_progress
        assert progress == {"filled": 0, "total": 0}


class TestGetCategoryProgressPartial:
    """get_category_progress() with some categories having checked items."""

    def test_some_categories_checked(self) -> None:
        """3 of 5 categories with checked items → filled=3, total=5."""
        bundle = _make_bundle(5)
        selections = {
            "cat_0": CategorySelections(checked_items=["a"], notes=""),
            "cat_1": CategorySelections(checked_items=["b"], notes=""),
            "cat_2": CategorySelections(checked_items=["c"], notes=""),
            # cat_3 and cat_4 not in selections
        }
        rs = _make_review_state(criteria_bundle=bundle, category_selections=selections)
        progress = rs.category_progress
        assert progress == {"filled": 3, "total": 5}

    def test_one_of_three_checked(self) -> None:
        """1 of 3 categories with checked items → filled=1, total=3."""
        bundle = _make_bundle(3)
        selections = {
            "cat_1": CategorySelections(checked_items=["x"], notes=""),
        }
        rs = _make_review_state(criteria_bundle=bundle, category_selections=selections)
        progress = rs.category_progress
        assert progress == {"filled": 1, "total": 3}

    def test_category_present_but_empty_checked_items(self) -> None:
        """Category in selections but with empty checked_items should NOT count as filled."""
        bundle = _make_bundle(2)
        selections = {
            "cat_0": CategorySelections(checked_items=[], notes="some notes"),
        }
        rs = _make_review_state(criteria_bundle=bundle, category_selections=selections)
        progress = rs.category_progress
        assert progress == {"filled": 0, "total": 2}


class TestGetCategoryProgressFull:
    """get_category_progress() with all categories having checked items."""

    def test_all_categories_checked(self) -> None:
        """All categories have at least one checked item → filled=N, total=N."""
        bundle = _make_bundle(4)
        selections = {
            f"cat_{i}": CategorySelections(checked_items=[f"item_{i}"], notes="") for i in range(4)
        }
        rs = _make_review_state(criteria_bundle=bundle, category_selections=selections)
        progress = rs.category_progress
        assert progress == {"filled": 4, "total": 4}

    def test_single_category_fully_checked(self) -> None:
        """Single category with checked items → filled=1, total=1."""
        bundle = _make_bundle(1)
        selections = {
            "cat_0": CategorySelections(checked_items=["a", "b"], notes=""),
        }
        rs = _make_review_state(criteria_bundle=bundle, category_selections=selections)
        progress = rs.category_progress
        assert progress == {"filled": 1, "total": 1}
