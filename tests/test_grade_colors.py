"""Tests for grade color utility functions."""

from src.utils.grade_colors import (
    card_grade_color_config,
    get_grade_color,
    sidebar_grade_color_config,
)


class TestGetGradeColor:
    """Tests for get_grade_color function."""

    def test_emerald_band(self) -> None:
        """1.0-1.7 returns emerald classes."""
        for grade in [1.0, 1.3, 1.7]:
            result = get_grade_color(grade)
            assert "emerald" in result, f"Grade {grade} should map to emerald"

    def test_blue_band(self) -> None:
        """2.0-2.7 returns blue classes."""
        for grade in [2.0, 2.3, 2.7]:
            result = get_grade_color(grade)
            assert "blue" in result, f"Grade {grade} should map to blue"

    def test_violet_band(self) -> None:
        """3.0-3.7 returns violet classes."""
        for grade in [3.0, 3.3, 3.7]:
            result = get_grade_color(grade)
            assert "violet" in result, f"Grade {grade} should map to violet"

    def test_amber_band(self) -> None:
        """4.0 returns amber classes."""
        result = get_grade_color(4.0)
        assert "amber" in result, "Grade 4.0 should map to amber"

    def test_red_band(self) -> None:
        """5.0 returns red classes."""
        result = get_grade_color(5.0)
        assert "red" in result, "Grade 5.0 should map to red"

    def test_boundary_values(self) -> None:
        """Boundary values at band edges produce correct colors."""
        assert "emerald" in get_grade_color(1.7)
        assert "blue" in get_grade_color(2.0)
        assert "blue" in get_grade_color(2.7)
        assert "violet" in get_grade_color(3.3)
        assert "violet" in get_grade_color(3.7)

    def test_below_range_defaults_to_emerald(self) -> None:
        """Grades below 1.0 default to emerald (best band)."""
        result = get_grade_color(0.5)
        assert "emerald" in result

    def test_above_range_defaults_to_red(self) -> None:
        """Grades above 5.0 default to red (worst band)."""
        result = get_grade_color(5.5)
        assert "red" in result


class TestSidebarGradeColorConfig:
    """Tests for sidebar_grade_color_config function."""

    def test_returns_dict_with_required_keys(self) -> None:
        """Config dict contains all required CSS class keys."""
        config = sidebar_grade_color_config(1.0)
        assert "bg_class" in config
        assert "text_class" in config
        assert "border_class" in config
        assert "ring_class" in config

    def test_emerald_sidebar_config(self) -> None:
        """Sidebar config for grade 1.0 uses emerald classes."""
        config = sidebar_grade_color_config(1.0)
        assert "emerald" in config["bg_class"]
        assert "emerald" in config["text_class"]

    def test_red_sidebar_config(self) -> None:
        """Sidebar config for grade 5.0 uses red classes."""
        config = sidebar_grade_color_config(5.0)
        assert "red" in config["bg_class"]
        assert "red" in config["text_class"]


class TestCardGradeColorConfig:
    """Tests for card_grade_color_config function."""

    def test_returns_dict_with_required_keys(self) -> None:
        """Config dict contains all required CSS class keys."""
        config = card_grade_color_config(1.0)
        assert "bg_class" in config
        assert "text_class" in config
        assert "border_class" in config
        assert "ring_class" in config

    def test_card_config_uses_subdued_greens(self) -> None:
        """Card config for grade 1.0 uses green-600/green-400 text."""
        config = card_grade_color_config(1.0)
        assert "green" in config["text_class"]

    def test_card_config_for_amber_grade(self) -> None:
        """Card config for grade 4.0 uses yellow classes."""
        config = card_grade_color_config(4.0)
        assert "yellow" in config["text_class"]
        assert "yellow" in config["border_class"]

    def test_card_config_for_red_grade(self) -> None:
        """Card config for grade 5.0 uses red classes."""
        config = card_grade_color_config(5.0)
        assert "red" in config["text_class"]
        assert "red" in config["border_class"]
