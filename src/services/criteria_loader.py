"""Load assignment definitions and criteria bundles from YAML files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.models.criteria import (
    AssignmentConfig,
    Category,
    CriteriaBundle,
    MainPoint,
    Sentiment,
    SubPoint,
)

# Default paths for YAML data files in the PyScript virtual filesystem.
DEFAULT_ASSIGNMENTS_PATH = "data/assignments.yaml"
DEFAULT_CRITERIA_DIR = "data/criteria/"


def _read_yaml(path: str) -> dict[str, Any] | None:
    """Read and parse a YAML file using standard open().

    Args:
        path: Path to the YAML file.

    Returns:
        Parsed YAML dict, or None if the file cannot be read.
    """
    # 1. Try the path as is (VFS in browser, or relative path in tests)
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except (FileNotFoundError, OSError):
        # 2. Fallback for local tests where files are in static/
        try:
            fallback_path = f"static/{path}"
            with open(fallback_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except (FileNotFoundError, OSError):
            return None


def _parse_sentiment_items(
    items: list[dict[str, Any]],
    sentiment: Sentiment,
) -> list[MainPoint]:
    """Parse a list of main_point/sub_points items into MainPoint objects.

    Args:
        items: List of dicts, each with 'main_point' str and 'sub_points' list.
        sentiment: Sentiment to assign to all resulting MainPoints.

    Returns:
        List of MainPoint objects.
    """
    main_points: list[MainPoint] = []
    for item in items:
        if not isinstance(item, dict) or "main_point" not in item:
            continue
        raw_text = item.get("main_point", "")
        text = str(raw_text) if raw_text else ""
        sub_points_raw = item.get("sub_points", [])
        sub_points = [
            SubPoint(text=sp["text"])
            for sp in sub_points_raw
            if isinstance(sp, dict) and "text" in sp and isinstance(sp["text"], str)
        ]
        main_points.append(
            MainPoint(
                text=text,
                sentiment=sentiment,
                sub_points=sub_points,
            )
        )
    return main_points


def _parse_single_category(
    slug: str,
    cat_data: dict[str, Any],
) -> Category:
    """Parse a single category dict into a Category model.

    Handles categories from both the 'general' section (keyed by slug)
    and 'assignment_specific' section (list with 'slug' field).

    Args:
        slug: Machine-readable category identifier.
        cat_data: Category data dict with 'title', 'positive', 'neutral',
            'negative'.

    Returns:
        A Category model instance.
    """
    title_raw = cat_data.get("title", slug)
    name = str(title_raw) if title_raw else slug
    main_points: list[MainPoint] = []

    for sentiment_str in ("positive", "neutral", "negative"):
        items = cat_data.get(sentiment_str, [])
        if isinstance(items, list):
            main_points.extend(_parse_sentiment_items(items, Sentiment(sentiment_str)))

    return Category(
        name=name,
        slug=slug,
        weight=0,
        main_points=main_points,
    )


def parse_criteria_yaml(
    data: dict[str, Any] | None,
    assignment_id: str,
    assignment_name: str,
) -> CriteriaBundle | None:
    """Parse criteria YAML data into a CriteriaBundle.

    Flattens the 'general' (dict keyed by slug) and 'assignment_specific'
    (list) sections into a single list of Category objects.

    Args:
        data: Parsed YAML data dict, or None.
        assignment_id: Unique assignment identifier.
        assignment_name: Human-readable assignment name.

    Returns:
        CriteriaBundle, or None if data is None.
    """
    if data is None:
        return None

    categories: list[Category] = []

    # Parse 'general' section (dict keyed by category slug).
    general = data.get("general")
    if isinstance(general, dict):
        for slug, cat_data in general.items():
            if isinstance(cat_data, dict):
                categories.append(_parse_single_category(slug, cat_data))

    # Parse 'assignment_specific' section (list of category dicts).
    assignment_specific = data.get("assignment_specific", [])
    if isinstance(assignment_specific, list):
        for idx, cat_data in enumerate(assignment_specific):
            if isinstance(cat_data, dict):
                slug_raw = cat_data.get("slug", "")
                slug = str(slug_raw) if slug_raw else f"specific_{idx}"
                categories.append(_parse_single_category(slug, cat_data))

    return CriteriaBundle(
        assignment_id=assignment_id,
        assignment_name=assignment_name,
        categories=categories,
    )


def parse_assignments_yaml(data: dict[str, Any] | None) -> list[AssignmentConfig]:
    """Parse assignments YAML data into a list of AssignmentConfig.

    Args:
        data: Parsed YAML data dict, or None.

    Returns:
        List of AssignmentConfig objects (empty if data is None or malformed).
    """
    if data is None:
        return []

    assignments_raw = data.get("assignments", [])
    if not isinstance(assignments_raw, list):
        return []

    assignments: list[AssignmentConfig] = []
    for item in assignments_raw:
        if not isinstance(item, dict):
            continue
        raw_id = item.get("id", "")
        if not raw_id:
            continue
        criteria_files = item.get("criteria_files", [])
        assignments.append(
            AssignmentConfig(
                id=str(raw_id),
                name=str(item.get("title", item.get("name", raw_id))),
                criteria_file=str(criteria_files[0])
                if isinstance(criteria_files, list) and criteria_files
                else "",
                enabled=bool(item.get("enabled", True)),
                max_points=int(item.get("max_points", 24)),
            )
        )
    return assignments


def load_assignments(path: str = DEFAULT_ASSIGNMENTS_PATH) -> list[AssignmentConfig]:
    """Load assignment definitions from a YAML file.

    Args:
        path: Path to the assignments YAML file.

    Returns:
        List of AssignmentConfig objects (empty if file not found).
    """
    data = _read_yaml(path)
    return parse_assignments_yaml(data)


def load_criteria_for_assignment(
    criteria_file: str,
    criteria_dir: str = DEFAULT_CRITERIA_DIR,
) -> CriteriaBundle | None:
    """Load a single criteria bundle from a YAML file.

    The assignment name is derived from the filename stem as a fallback.

    Args:
        criteria_file: Filename of the criteria YAML file.
        criteria_dir: Directory containing criteria YAML files.

    Returns:
        CriteriaBundle, or None if the file cannot be read.
    """
    path = criteria_dir.rstrip("/") + "/" + criteria_file.lstrip("/")
    data = _read_yaml(path)
    if data is None:
        return None
    stem = Path(criteria_file).stem
    return parse_criteria_yaml(data, stem, stem)


def load_all_criteria(
    assignments_path: str = DEFAULT_ASSIGNMENTS_PATH,
    criteria_dir: str = DEFAULT_CRITERIA_DIR,
) -> list[CriteriaBundle]:
    """Load criteria bundles for all enabled assignments.

    Args:
        assignments_path: Path to the assignments YAML file.
        criteria_dir: Directory containing criteria YAML files.

    Returns:
        List of CriteriaBundle objects for enabled assignments
        (empty list if no assignments or all disabled).
    """
    assignments = load_assignments(assignments_path)
    bundles: list[CriteriaBundle] = []
    for assignment in assignments:
        if not assignment.enabled:
            continue
        crit_rel = Path(assignment.criteria_file).name
        data = _read_yaml(criteria_dir.rstrip("/") + "/" + crit_rel)
        bundle = parse_criteria_yaml(data, assignment.id, assignment.name)
        if bundle is not None:
            bundles.append(bundle)
    return bundles


def get_criteria_for_assignment(
    assignment_id: str,
    assignments_path: str = DEFAULT_ASSIGNMENTS_PATH,
    criteria_dir: str = DEFAULT_CRITERIA_DIR,
) -> CriteriaBundle | None:
    """Get criteria bundle for a specific assignment, merging general.yaml.

    Args:
        assignment_id: Assignment identifier.
        assignments_path: Path to the assignments YAML file.
        criteria_dir: Directory containing criteria YAML files.

    Returns:
        CriteriaBundle, or None if the assignment is not found or disabled.
    """
    assignments = load_assignments(assignments_path)
    for assignment in assignments:
        if assignment.id == assignment_id and assignment.enabled:
            # 1. Load general.yaml as base
            general_data = _read_yaml(criteria_dir.rstrip("/") + "/general.yaml") or {}

            # 2. Load assignment specific file
            crit_rel = Path(assignment.criteria_file).name
            assignment_data = _read_yaml(criteria_dir.rstrip("/") + "/" + crit_rel) or {}

            # 3. Merge data
            merged_data: dict[str, Any] = {"general": {}, "assignment_specific": []}

            # Merge general sections (dicts)
            merged_data["general"].update(general_data.get("general", {}))
            merged_data["general"].update(assignment_data.get("general", {}))

            # Merge assignment_specific sections (lists)
            merged_data["assignment_specific"].extend(general_data.get("assignment_specific", []))
            merged_data["assignment_specific"].extend(
                assignment_data.get("assignment_specific", [])
            )

            return parse_criteria_yaml(merged_data, assignment.id, assignment.name)
    return None


def get_assignments_from_criteria(
    path: str = DEFAULT_ASSIGNMENTS_PATH,
) -> list[AssignmentConfig]:
    """Get list of enabled assignments.

    Args:
        path: Path to the assignments YAML file.

    Returns:
        List of enabled AssignmentConfig objects.
    """
    assignments = load_assignments(path)
    return [a for a in assignments if a.enabled]


# -- Aliases for consistency with components --------------------------------

load_criteria_bundle = get_criteria_for_assignment
load_assignments_list = get_assignments_from_criteria
