"""Pydantic models for criteria YAML parsing and validation."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Sentiment(StrEnum):
    """Sentiment direction of a rubric point."""

    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class SubPoint(BaseModel):
    """A single selectable sub-point under a main rubric point."""

    text: str = Field(description="Display text shown to the grader")
    id: str | None = Field(
        default=None,
        description="Optional unique identifier for the sub-point",
    )


class MainPoint(BaseModel):
    """A main rubric point grouping related sub-points."""

    text: str = Field(description="Heading text for the main point")
    sentiment: Sentiment = Field(
        description="Sentiment direction of this main point",
    )
    sub_points: list[SubPoint] = Field(
        default_factory=list,
        description="List of selectable sub-points belonging to this group",
    )


class Category(BaseModel):
    """A rubric category containing graded main points."""

    name: str = Field(description="Human-readable name of the category")
    slug: str = Field(description="Machine-readable identifier for the category")
    weight: int = Field(description="Weight of the category in overall grading")
    main_points: list[MainPoint] = Field(
        description="List of main points in this category",
    )


class CriteriaBundle(BaseModel):
    """Complete rubric criteria bundle for an assignment."""

    assignment_id: str = Field(
        description="Unique identifier for the assignment",
    )
    assignment_name: str = Field(
        description="Human-readable name of the assignment",
    )
    categories: list[Category] = Field(
        description="List of rubric categories",
    )


class AssignmentConfig(BaseModel):
    """Configuration for a single assignment."""

    id: str = Field(description="Machine-readable assignment identifier")
    name: str = Field(description="Human-readable assignment title")
    criteria_file: str = Field(
        description="Path to the YAML criteria file defining the rubric",
    )
    enabled: bool = Field(
        default=True,
        description="Whether the assignment is available for selection",
    )
    max_points: int = Field(
        default=24,
        description="Maximum total points for the assignment",
    )
