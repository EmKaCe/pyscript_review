"""Tests for criteria YAML loading and parsing."""

from __future__ import annotations

import pytest
from src.models.criteria import (
    CriteriaBundle,
    Sentiment,
)
from src.services.criteria_loader import (
    get_assignments_from_criteria,
    get_criteria_for_assignment,
    load_all_criteria,
    load_assignments,
    load_criteria_for_assignment,
    parse_assignments_yaml,
    parse_criteria_yaml,
)


class TestParseCriteriaYaml:
    """Tests for parse_criteria_yaml."""

    def test_none_data_returns_none(self) -> None:
        """Passing None must return None."""
        result = parse_criteria_yaml(None, "test", "Test")
        assert result is None

    def test_empty_data_returns_bundle_without_categories(self) -> None:
        """Empty dict must produce a bundle with no categories."""
        result = parse_criteria_yaml({}, "test", "Test")
        assert isinstance(result, CriteriaBundle)
        assert result.assignment_id == "test"
        assert result.assignment_name == "Test"
        assert result.categories == []

    def test_general_section_parsed_into_categories(self) -> None:
        """General section entries must become Category objects."""
        data = {
            "general": {
                "codeFormatting": {
                    "title": "Code Formatting",
                    "positive": [
                        {
                            "main_point": "Formatting is good",
                            "sub_points": [{"text": "good indentation"}],
                        }
                    ],
                    "neutral": [],
                    "negative": [],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories) == 1
        cat = result.categories[0]
        assert cat.slug == "codeFormatting"
        assert cat.name == "Code Formatting"
        assert len(cat.main_points) == 1
        assert cat.main_points[0].text == "Formatting is good"
        assert cat.main_points[0].sentiment == Sentiment.POSITIVE
        assert len(cat.main_points[0].sub_points) == 1
        assert cat.main_points[0].sub_points[0].text == "good indentation"

    def test_assignment_specific_parsed(self) -> None:
        """Assignment-specific section items must become Category objects."""
        data = {
            "general": {},
            "assignment_specific": [
                {
                    "slug": "userDefinedFunctions",
                    "title": "User-defined Functions",
                    "additional_notes": True,
                    "positive": [
                        {
                            "main_point": "Good use",
                            "sub_points": [{"text": "docstring context"}],
                        }
                    ],
                    "neutral": [],
                    "negative": [],
                }
            ],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories) == 1
        cat = result.categories[0]
        assert cat.slug == "userDefinedFunctions"
        assert cat.name == "User-defined Functions"
        assert len(cat.main_points) == 1
        assert cat.main_points[0].sentiment == Sentiment.POSITIVE

    def test_sentiment_mapping_positive_neutral_negative(self) -> None:
        """All three sentiments must map correctly."""
        data = {
            "general": {
                "cat1": {
                    "title": "Category",
                    "positive": [
                        {
                            "main_point": "Good",
                            "sub_points": [{"text": "well done"}],
                        }
                    ],
                    "neutral": [
                        {
                            "main_point": "Okay",
                            "sub_points": [{"text": "acceptable"}],
                        }
                    ],
                    "negative": [
                        {
                            "main_point": "Bad",
                            "sub_points": [{"text": "needs work"}],
                        }
                    ],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        cat = result.categories[0]
        sentiments = {mp.text: mp.sentiment for mp in cat.main_points}
        assert sentiments["Good"] == Sentiment.POSITIVE
        assert sentiments["Okay"] == Sentiment.NEUTRAL
        assert sentiments["Bad"] == Sentiment.NEGATIVE

    def test_multiple_main_points_per_sentiment(self) -> None:
        """Multiple main_points in the same sentiment must all be included."""
        data = {
            "general": {
                "cat1": {
                    "title": "Category",
                    "positive": [
                        {
                            "main_point": "First good",
                            "sub_points": [{"text": "a"}],
                        },
                        {
                            "main_point": "Second good",
                            "sub_points": [{"text": "b"}],
                        },
                    ],
                    "neutral": [],
                    "negative": [],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories[0].main_points) == 2

    def test_skips_malformed_main_point_items(self) -> None:
        """Items without 'main_point' key or non-dict items must be skipped."""
        data = {
            "general": {
                "cat1": {
                    "title": "Category",
                    "positive": [
                        {"main_point": "Valid", "sub_points": [{"text": "ok"}]},
                        {"not_main_point": "Invalid"},
                        "string_item",
                        123,
                    ],
                    "neutral": [],
                    "negative": [],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories[0].main_points) == 1

    def test_skips_sub_points_without_text(self) -> None:
        """Sub-point dicts missing 'text' must be skipped."""
        data = {
            "general": {
                "cat1": {
                    "title": "Category",
                    "positive": [
                        {
                            "main_point": "Good",
                            "sub_points": [
                                {"text": "valid"},
                                {"comment": True},
                                {},
                            ],
                        }
                    ],
                    "neutral": [],
                    "negative": [],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories[0].main_points[0].sub_points) == 1
        assert result.categories[0].main_points[0].sub_points[0].text == "valid"

    def test_assignment_specific_missing_slug_uses_index(self) -> None:
        """Categories in assignment_specific without slug get an auto-generated slug."""
        data = {
            "general": {},
            "assignment_specific": [
                {
                    "title": "Custom",
                    "positive": [
                        {
                            "main_point": "Done well",
                            "sub_points": [{"text": "nice"}],
                        }
                    ],
                    "neutral": [],
                    "negative": [],
                }
            ],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories) == 1
        assert result.categories[0].slug == "specific_0"

    def test_no_main_point_text_uses_empty_string(self) -> None:
        """Main point with empty or missing text should use empty string."""
        data = {
            "general": {
                "cat1": {
                    "title": "Category",
                    "positive": [
                        {
                            "main_point": "",
                            "sub_points": [{"text": "item"}],
                        }
                    ],
                    "neutral": [],
                    "negative": [],
                }
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert result.categories[0].main_points[0].text == ""


class TestParseAssignmentsYaml:
    """Tests for parse_assignments_yaml."""

    def test_none_returns_empty_list(self) -> None:
        """None data must return empty list."""
        assert parse_assignments_yaml(None) == []

    def test_empty_dict_returns_empty_list(self) -> None:
        """Empty dict must return empty list."""
        assert parse_assignments_yaml({}) == []

    def test_parses_single_assignment(self) -> None:
        """A single assignment must parse correctly."""
        data = {
            "assignments": [
                {
                    "id": "user_function",
                    "title": "User Function",
                    "criteria_files": ["data/criteria/user_function.yaml"],
                    "enabled": True,
                }
            ]
        }
        result = parse_assignments_yaml(data)
        assert len(result) == 1
        assert result[0].id == "user_function"
        assert result[0].name == "User Function"
        assert result[0].criteria_file == "data/criteria/user_function.yaml"
        assert result[0].enabled is True
        assert result[0].max_points == 24

    def test_multiple_assignments(self) -> None:
        """Multiple assignments must all be parsed."""
        data = {
            "assignments": [
                {
                    "id": "a1",
                    "title": "Assign 1",
                    "criteria_files": ["c1.yaml"],
                    "enabled": True,
                },
                {
                    "id": "a2",
                    "title": "Assign 2",
                    "criteria_files": ["c2.yaml"],
                    "enabled": False,
                },
            ]
        }
        result = parse_assignments_yaml(data)
        assert len(result) == 2
        assert result[0].id == "a1"
        assert result[1].id == "a2"

    def test_uses_first_criteria_file(self) -> None:
        """Only the first entry in criteria_files list must be used."""
        data = {
            "assignments": [
                {
                    "id": "test",
                    "title": "Test",
                    "criteria_files": [
                        "primary.yaml",
                        "secondary.yaml",
                    ],
                    "enabled": True,
                }
            ]
        }
        result = parse_assignments_yaml(data)
        assert len(result) == 1
        assert result[0].criteria_file == "primary.yaml"

    def test_skips_items_missing_id(self) -> None:
        """Items without an id must be skipped."""
        data = {
            "assignments": [
                {
                    "title": "No ID",
                    "criteria_files": ["c.yaml"],
                    "enabled": True,
                },
                {
                    "id": "valid",
                    "title": "Valid",
                    "criteria_files": ["c.yaml"],
                    "enabled": True,
                },
            ]
        }
        result = parse_assignments_yaml(data)
        assert len(result) == 1
        assert result[0].id == "valid"

    def test_skips_non_dict_items(self) -> None:
        """Non-dict items in the assignments list must be skipped."""
        data = {
            "assignments": [
                {"id": "valid", "title": "Valid", "criteria_files": ["c.yaml"], "enabled": True},
                "string_item",
                42,
            ]
        }
        result = parse_assignments_yaml(data)
        assert len(result) == 1
        assert result[0].id == "valid"

    def test_falls_back_title_from_name(self) -> None:
        """If no title key, falls back to 'name', then to id."""
        data = {
            "assignments": [
                {
                    "id": "fallback_test",
                    "name": "From Name",
                    "criteria_files": ["c.yaml"],
                    "enabled": True,
                }
            ]
        }
        result = parse_assignments_yaml(data)
        assert result[0].name == "From Name"

    def test_defaults(self) -> None:
        """Assignment with missing optional fields must use defaults."""
        data = {
            "assignments": [
                {
                    "id": "minimal",
                    "title": "Minimal",
                    "criteria_files": ["c.yaml"],
                }
            ]
        }
        result = parse_assignments_yaml(data)
        assert result[0].enabled is True
        assert result[0].max_points == 24
        assert result[0].criteria_file == "c.yaml"


class TestParseRealYamlStructure:
    """Tests that parse real-world YAML structures (no file I/O)."""

    def test_general_yaml_structure(self) -> None:
        """Parse the general.yaml structure passed as inline dict."""
        data = {
            "general": {
                "codeFormatting": {
                    "title": "Code Formatting",
                    "positive": [
                        {
                            "main_point": "Formatting is done well, which includes",
                            "sub_points": [
                                {"text": "blank lines - consistent and good usage"},
                                {"text": "concise, clean and clearly written code"},
                                {"text": "commenting - appropriate amount provided"},
                            ],
                        }
                    ],
                    "neutral": [],
                    "negative": [
                        {
                            "main_point": "The following formatting issues were present",
                            "sub_points": [
                                {"text": "blank lines - missing the required two blank lines"},
                                {"text": "blank lines - not enough used"},
                            ],
                        }
                    ],
                },
                "codingConcept": {
                    "title": "Coding Concept",
                    "positive": [
                        {
                            "main_point": "Data structures done well",
                            "sub_points": [
                                {"text": "dictionary"},
                                {"text": "list"},
                            ],
                        }
                    ],
                    "neutral": [],
                    "negative": [
                        {
                            "main_point": "Better data structures would have improved",
                            "sub_points": [
                                {"text": "looping - over a dictionary"},
                            ],
                        }
                    ],
                },
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "test", "Test")
        assert result is not None
        assert len(result.categories) == 2

        # codeFormatting
        cf = result.categories[0]
        assert cf.slug == "codeFormatting"
        assert cf.name == "Code Formatting"

        # Check positive main_points in codeFormatting
        pos_mps = [mp for mp in cf.main_points if mp.sentiment == Sentiment.POSITIVE]
        assert len(pos_mps) == 1
        assert "Formatting is done well" in pos_mps[0].text

        # Check negative main_points in codeFormatting
        neg_mps = [mp for mp in cf.main_points if mp.sentiment == Sentiment.NEGATIVE]
        assert len(neg_mps) == 1

        # codingConcept
        cc = result.categories[1]
        assert cc.slug == "codingConcept"
        assert cc.name == "Coding Concept"

        neg_cc = [mp for mp in cc.main_points if mp.sentiment == Sentiment.NEGATIVE]
        assert len(neg_cc) == 1
        assert "Better data structures" in neg_cc[0].text

    def test_user_function_yaml_structure(self) -> None:
        """Parse the user_function.yaml structure (assignment specific)."""
        data = {
            "general": {
                "userDefinedFunctions": {
                    "title": "User-defined Functions",
                    "positive": [
                        {
                            "main_point": "Good use of the following",
                            "sub_points": [
                                {"text": "docstring - providing context"},
                                {"text": "type hinting - applied well"},
                            ],
                        }
                    ],
                    "neutral": [
                        {
                            "main_point": "Okay user-defined function(s), but",
                            "sub_points": [
                                {"text": "assert vs. raise"},
                            ],
                        }
                    ],
                    "negative": [
                        {
                            "main_point": "No user-defined functions employed",
                            "sub_points": [
                                {"text": "Your solution did not include user-defined functions"},
                            ],
                        },
                        {
                            "main_point": "Your user-defined functions had the following problems",
                            "sub_points": [
                                {"text": "complex - too many ideas"},
                                {"text": "docstring - none provided"},
                            ],
                        },
                    ],
                },
                "callingFunction": {
                    "title": "Function (and Method) Calling",
                    "positive": [],
                    "neutral": [],
                    "negative": [
                        {
                            "main_point": "",
                            "sub_points": [
                                {"text": "formatting - placing each parameter"},
                            ],
                        }
                    ],
                },
            },
            "assignment_specific": [],
        }
        result = parse_criteria_yaml(data, "user_function", "User Function")
        assert result is not None
        assert result.assignment_id == "user_function"
        assert result.assignment_name == "User Function"
        assert len(result.categories) == 2

        # userDefinedFunctions has 4 main_points (1 pos + 1 neutral + 2 neg)
        uda = result.categories[0]
        assert uda.slug == "userDefinedFunctions"
        assert len(uda.main_points) == 4

        # callingFunction has 1 negative, empty pos/neutral
        cf = result.categories[1]
        assert cf.slug == "callingFunction"
        assert len(cf.main_points) == 1
        assert cf.main_points[0].sentiment == Sentiment.NEGATIVE


class TestLoadFunctions:
    """Tests for file-loading functions (load_assignments, etc.)."""

    def test_load_assignments_from_yaml(self, tmp_path: pytest.TempPathFactory) -> None:
        """load_assignments must parse a real YAML file on disk."""
        yaml_path = tmp_path / "assignments.yaml"
        yaml_path.write_text(
            "assignments:\n"
            "- id: test_a\n"
            "  title: Test A\n"
            "  criteria_files:\n"
            "  - data/criteria/test_a.yaml\n"
            "  enabled: true\n"
            "- id: test_b\n"
            "  title: Test B\n"
            "  criteria_files:\n"
            "  - data/criteria/test_b.yaml\n"
            "  enabled: false\n",
            encoding="utf-8",
        )
        result = load_assignments(str(yaml_path))
        assert len(result) == 2
        assert result[0].id == "test_a"
        assert result[0].enabled is True
        assert result[1].id == "test_b"
        assert result[1].enabled is False

    def test_load_assignments_missing_file_returns_empty(self) -> None:
        """Missing file must return empty list, not crash."""
        result = load_assignments("/nonexistent/path/assignments.yaml")
        assert result == []

    def test_load_criteria_missing_file_returns_none(self) -> None:
        """Missing criteria file must return None, not crash."""
        result = load_criteria_for_assignment("nonexistent.yaml", "/nonexistent/criteria/")
        assert result is None

    def test_load_all_criteria_no_assignments_returns_empty(self) -> None:
        """No assignments file must return empty list."""
        result = load_all_criteria("/nonexistent/assignments.yaml")
        assert result == []

    def test_get_criteria_missing_assignment_returns_none(self) -> None:
        """Unknown assignment ID must return None."""
        result = get_criteria_for_assignment("nonexistent", "/nonexistent/assignments.yaml")
        assert result is None

    def test_get_assignments_from_criteria_only_enabled(
        self, tmp_path: pytest.TempPathFactory
    ) -> None:
        """get_assignments_from_criteria must filter to enabled only."""
        yaml_path = tmp_path / "assignments.yaml"
        yaml_path.write_text(
            "assignments:\n"
            "- id: enabled_a\n"
            "  title: Enabled A\n"
            "  criteria_files:\n"
            "  - a.yaml\n"
            "  enabled: true\n"
            "- id: disabled_b\n"
            "  title: Disabled B\n"
            "  criteria_files:\n"
            "  - b.yaml\n"
            "  enabled: false\n",
            encoding="utf-8",
        )
        result = get_assignments_from_criteria(str(yaml_path))
        assert len(result) == 1
        assert result[0].id == "enabled_a"

    def test_load_all_criteria_skips_disabled(self, tmp_path: pytest.TempPathFactory) -> None:
        """load_all_criteria must skip disabled assignments."""
        yaml_path = tmp_path / "assignments.yaml"
        yaml_path.write_text(
            "assignments:\n"
            "- id: disabled_a\n"
            "  title: Disabled\n"
            "  criteria_files:\n"
            "  - data/criteria/a.yaml\n"
            "  enabled: false\n",
            encoding="utf-8",
        )
        # No criteria file exists, but it won't be loaded since disabled
        result = load_all_criteria(str(yaml_path))
        assert result == []

    def test_load_and_parse_criteria(self, tmp_path: pytest.TempPathFactory) -> None:
        """End-to-end: load assignments, then load criteria."""
        assignments_yaml = tmp_path / "assignments.yaml"
        assignments_yaml.write_text(
            "assignments:\n"
            "- id: test_criteria\n"
            "  title: Test Criteria\n"
            "  criteria_files:\n"
            "  - data/criteria/test_criteria.yaml\n"
            "  enabled: true\n",
            encoding="utf-8",
        )

        criteria_dir = tmp_path / "data" / "criteria"
        criteria_dir.mkdir(parents=True)
        criteria_file = criteria_dir / "test_criteria.yaml"
        criteria_file.write_text(
            "general:\n"
            "  formatting:\n"
            "    title: Formatting\n"
            "    positive:\n"
            "    - main_point: Good formatting\n"
            "      sub_points:\n"
            "      - text: indentation\n"
            "    neutral: []\n"
            "    negative: []\n"
            "assignment_specific: []\n",
            encoding="utf-8",
        )

        bundles = load_all_criteria(str(assignments_yaml), str(criteria_dir) + "/")
        assert len(bundles) == 1
        assert bundles[0].assignment_id == "test_criteria"
        assert bundles[0].assignment_name == "Test Criteria"
        assert len(bundles[0].categories) == 1
        assert bundles[0].categories[0].slug == "formatting"
        assert len(bundles[0].categories[0].main_points) == 1

    def test_get_criteria_for_specific_assignment(self, tmp_path: pytest.TempPathFactory) -> None:
        """get_criteria_for_assignment must return the correct bundle."""
        assignments_yaml = tmp_path / "assignments.yaml"
        assignments_yaml.write_text(
            "assignments:\n"
            "- id: a1\n"
            "  title: Assignment 1\n"
            "  criteria_files:\n"
            "  - a1.yaml\n"
            "  enabled: true\n"
            "- id: a2\n"
            "  title: Assignment 2\n"
            "  criteria_files:\n"
            "  - a2.yaml\n"
            "  enabled: true\n",
            encoding="utf-8",
        )

        criteria_dir = tmp_path / "criteria"
        criteria_dir.mkdir()
        (criteria_dir / "a1.yaml").write_text(
            "general:\n"
            "  catA:\n"
            "    title: Cat A\n"
            "    positive:\n"
            "    - main_point: A stuff\n"
            "      sub_points:\n"
            "      - text: good\n"
            "    neutral: []\n"
            "    negative: []\n"
            "assignment_specific: []\n",
            encoding="utf-8",
        )
        (criteria_dir / "a2.yaml").write_text(
            "general:\n"
            "  catB:\n"
            "    title: Cat B\n"
            "    positive:\n"
            "    - main_point: B stuff\n"
            "      sub_points:\n"
            "      - text: nice\n"
            "    neutral: []\n"
            "    negative: []\n"
            "assignment_specific: []\n",
            encoding="utf-8",
        )

        result = get_criteria_for_assignment("a1", str(assignments_yaml), str(criteria_dir) + "/")
        assert result is not None
        assert result.assignment_id == "a1"
        assert result.categories[0].slug == "catA"

        result_a2 = get_criteria_for_assignment(
            "a2", str(assignments_yaml), str(criteria_dir) + "/"
        )
        assert result_a2 is not None
        assert result_a2.assignment_id == "a2"
        assert result_a2.categories[0].slug == "catB"
