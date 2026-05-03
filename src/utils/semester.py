"""Utilities for determining academic semesters and extracting semester info

from student identifiers.

German university semester conventions:
  - SS (Sommersemester): April 1 - July 31
  - WS (Wintersemester): October 1 - February 28/29
  - Between semesters (August, September, March): return the upcoming semester.
"""

import re
from datetime import date


def get_current_semester(d: date | None = None) -> str:
    """Return the current academic semester string.

    Args:
        d: Date to derive the semester from; defaults to today.

    Returns:
        Semester string like "SS25" or "WS2425".
    """
    d = d or date.today()
    year = d.year
    month = d.month

    if month in (4, 5, 6, 7):
        # SS: April - July
        return f"SS{year % 100:02d}"
    elif month in (10, 11, 12):
        # WS: October - December
        return f"WS{year % 100:02d}{(year + 1) % 100:02d}"
    elif month in (1, 2):
        # WS: January - February
        return f"WS{(year - 1) % 100:02d}{year % 100:02d}"
    elif month == 3:
        # March: between semesters, next is SS
        return f"SS{year % 100:02d}"
    else:  # month in (8, 9)
        # August, September: between semesters, next is WS
        return f"WS{year % 100:02d}{(year + 1) % 100:02d}"


def extract_semester(student_id: str) -> str | None:
    """Extract the semester code from a student identifier.

    Student IDs have formats like "1234WS2425" or "5678SS25" where the
    semester suffix is at the end of the string.

    Args:
        student_id: Student identifier string.

    Returns:
        Extracted semester code (e.g. "WS2425", "SS25") or None if no match.
    """
    match = re.search(r"(WS\d{4}|SS\d{2})$", student_id)
    return match.group(1) if match else None


def parse_semester(semester_str: str) -> tuple[str, int] | None:
    """Parse a semester string into its type and start year.

    Args:
        semester_str: Semester string like "WS2425" or "SS25".

    Returns:
        Tuple of (semester_type, start_year), e.g. ("WS", 2024) or
        ("SS", 2025). Returns None if the format is invalid.
    """
    if semester_str.startswith("WS") and len(semester_str) == 6:
        year = int("20" + semester_str[2:4])
        return ("WS", year)
    elif semester_str.startswith("SS") and len(semester_str) == 4:
        year = int("20" + semester_str[2:4])
        return ("SS", year)
    return None


def semester_display(semester_str: str) -> str:
    """Format a semester string for human-readable display.

    Args:
        semester_str: Semester string like "WS2425" or "SS25".

    Returns:
        Human-readable format like "WS 2024/25" or "SS 2025".
    """
    parsed = parse_semester(semester_str)
    if parsed is None:
        return semester_str
    prefix, year = parsed
    if prefix == "WS":
        return f"WS {year}/{str(year + 1)[-2:]}"
    return f"SS {year}"
