"""Text generation service for producing structured evaluation text.

Generates markdown-style plain text from review rubric selections,
matching the Svelte text-generator.ts output format.
"""

from __future__ import annotations

from src.models.criteria import CriteriaBundle, Sentiment
from src.models.session import ReviewSession


def _group_by_sentiment(
    session: ReviewSession,
    criteria_bundle: CriteriaBundle,
) -> dict[str, dict[str, list[str]]]:
    """Group checked sub-point texts by sentiment, then by category name.

    Scoped key format: ``{category_slug}::{sentiment}::{sub_point_text}``

    Args:
        session: The review session with selections and metadata.
        criteria_bundle: The criteria definitions for the assignment.

    Returns:
        Nested dict: sentiment -> category_name -> list of item texts.
    """
    groups: dict[str, dict[str, list[str]]] = {
        Sentiment.POSITIVE.value: {},
        Sentiment.NEUTRAL.value: {},
        Sentiment.NEGATIVE.value: {},
    }

    for category in criteria_bundle.categories:
        selections = session.category_selections.get(category.slug)
        if selections is None or not selections.checked_items:
            continue

        checked_set = set(selections.checked_items)

        for main_point in category.main_points:
            sentiment_key = main_point.sentiment.value
            for sub_point in main_point.sub_points:
                scoped_key = f"{category.slug}::{sentiment_key}::{sub_point.text}"
                if scoped_key in checked_set:
                    if category.name not in groups[sentiment_key]:
                        groups[sentiment_key][category.name] = []
                    groups[sentiment_key][category.name].append(sub_point.text)

    return groups


def _build_section(
    lines: list[str],
    heading: str,
    groups: dict[str, list[str]],
) -> None:
    """Append a sentiment section to the output lines.

    Args:
        lines: The output line accumulator.
        heading: The section heading text.
        groups: Category name -> list of item texts for this sentiment.
    """
    if not groups:
        return

    lines.append(f"## {heading}")
    lines.append("")

    for cat_name in groups:
        lines.append(f"**{cat_name}**")
        for item_text in groups[cat_name]:
            lines.append(f"  \u2022 {item_text}")
        lines.append("")


def generate_evaluation_text(
    session: ReviewSession,
    criteria_bundle: CriteriaBundle,
) -> str:
    """Generate structured evaluation text from review rubric selections.

    Produces a plain-text report with three sections — Positive Observations,
    General Observations, and Areas for Improvement — grouped by rubric
    category. Includes additional notes if any category has non-empty notes.

    Args:
        session: The review session with selections and metadata.
        criteria_bundle: The criteria definitions for the assignment.

    Returns:
        Formatted evaluation string suitable for display or export.
    """
    lines: list[str] = []

    lines.append(
        f"Evaluation for {session.student_id} \u2014 {session.assignment_id}",
    )
    lines.append("=" * 50)
    lines.append("")

    groups = _group_by_sentiment(session, criteria_bundle)

    _build_section(lines, "Positive Observations", groups[Sentiment.POSITIVE.value])
    _build_section(lines, "General Observations", groups[Sentiment.NEUTRAL.value])
    _build_section(lines, "Areas for Improvement", groups[Sentiment.NEGATIVE.value])

    # Collect additional notes for categories that have non-empty notes.
    notes_entries: list[tuple[str, str]] = []
    for category in criteria_bundle.categories:
        selections = session.category_selections.get(category.slug)
        if selections is not None and selections.notes.strip():
            notes_entries.append((category.name, selections.notes))

    if notes_entries:
        lines.append("## Additional Notes")
        lines.append("")
        for cat_name, notes in notes_entries:
            lines.append(f"**{cat_name}**: {notes}")

    return "\n".join(lines)
