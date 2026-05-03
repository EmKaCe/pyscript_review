"""Tests for semester utility functions."""

from datetime import date

from src.utils.semester import (
    extract_semester,
    get_current_semester,
    parse_semester,
    semester_display,
)


class TestGetCurrentSemester:
    """Tests for get_current_semester()."""

    def test_ss_april(self):
        """April should return SS with current year."""
        result = get_current_semester(date(2025, 4, 15))
        assert result == "SS25"

    def test_ss_july(self):
        """July should return SS with current year."""
        result = get_current_semester(date(2025, 7, 1))
        assert result == "SS25"

    def test_ws_october(self):
        """October should return WS with current and next year."""
        result = get_current_semester(date(2025, 10, 1))
        assert result == "WS2526"

    def test_ws_december(self):
        """December should return WS with current and next year."""
        result = get_current_semester(date(2025, 12, 31))
        assert result == "WS2526"

    def test_ws_january(self):
        """January should return WS with previous and current year."""
        result = get_current_semester(date(2026, 1, 15))
        assert result == "WS2526"

    def test_ws_february(self):
        """February should return WS with previous and current year."""
        result = get_current_semester(date(2026, 2, 28))
        assert result == "WS2526"

    def test_march_next_ss(self):
        """March should return upcoming SS (between semesters)."""
        result = get_current_semester(date(2025, 3, 15))
        assert result == "SS25"

    def test_august_next_ws(self):
        """August should return upcoming WS (between semesters)."""
        result = get_current_semester(date(2025, 8, 15))
        assert result == "WS2526"

    def test_september_next_ws(self):
        """September should return upcoming WS (between semesters)."""
        result = get_current_semester(date(2025, 9, 1))
        assert result == "WS2526"

    def test_year_boundary_december_to_january(self):
        """December 2026 WS should lead into 2027."""
        result = get_current_semester(date(2026, 12, 1))
        assert result == "WS2627"

    def test_year_boundary_january(self):
        """January 2027 should refer back to WS 2026/27."""
        result = get_current_semester(date(2027, 1, 1))
        assert result == "WS2627"

    def test_cross_century(self):
        """Year 2099 should handle two-digit year formatting."""
        result = get_current_semester(date(2099, 10, 1))
        assert result == "WS9900"

    def test_valid_format(self):
        """Result should always match SSxx or xxxx format."""
        for month in range(1, 13):
            result = get_current_semester(date(2025, month, 15))
            assert result[:2] in ("SS", "WS")
            assert result[2:].isdigit()


class TestExtractSemester:
    """Tests for extract_semester()."""

    def test_ws_format(self):
        """WS2425 at end of ID should be extracted."""
        result = extract_semester("1234WS2425")
        assert result == "WS2425"

    def test_ss_format(self):
        """SS25 at end of ID should be extracted."""
        result = extract_semester("5678SS25")
        assert result == "SS25"

    def test_no_semester(self):
        """ID without semester suffix returns None."""
        result = extract_semester("12345")
        assert result is None

    def test_empty_string(self):
        """Empty string returns None."""
        result = extract_semester("")
        assert result is None

    def test_invalid_format(self):
        """Invalid semester format returns None."""
        result = extract_semester("1234XX25")
        assert result is None

    def test_semester_in_middle(self):
        """Semester code in middle (not at end) returns None."""
        result = extract_semester("WS2425extra")
        assert result is None


class TestParseSemester:
    """Tests for parse_semester()."""

    def test_ws_format(self):
        """WS2425 should parse to ('WS', 2024)."""
        result = parse_semester("WS2425")
        assert result == ("WS", 2024)

    def test_ss_format(self):
        """SS25 should parse to ('SS', 2025)."""
        result = parse_semester("SS25")
        assert result == ("SS", 2025)

    def test_invalid_format(self):
        """Invalid format returns None."""
        result = parse_semester("XX25")
        assert result is None

    def test_empty_string(self):
        """Empty string returns None."""
        result = parse_semester("")
        assert result is None

    def test_ws_short(self):
        """WS without full format returns None."""
        result = parse_semester("WS25")
        assert result is None

    def test_ss_long(self):
        """SS with 4 digits returns None (SS format is 2 digits)."""
        result = parse_semester("SS2526")
        assert result is None

    def test_ws_year_2000(self):
        """WS9900 should parse to ('WS', 2099)."""
        result = parse_semester("WS9900")
        assert result == ("WS", 2099)

    def test_ss_year_2000(self):
        """SS00 should parse to ('SS', 2000)."""
        result = parse_semester("SS00")
        assert result == ("SS", 2000)


class TestSemesterDisplay:
    """Tests for semester_display()."""

    def test_ws_format(self):
        """WS2425 should display as 'WS 2024/25'."""
        result = semester_display("WS2425")
        assert result == "WS 2024/25"

    def test_ss_format(self):
        """SS25 should display as 'SS 2025'."""
        result = semester_display("SS25")
        assert result == "SS 2025"

    def test_invalid_format(self):
        """Invalid format should be returned as-is."""
        result = semester_display("invalid")
        assert result == "invalid"

    def test_ws_cross_century(self):
        """WS9900 should display as 'WS 2099/00'."""
        result = semester_display("WS9900")
        assert result == "WS 2099/00"
