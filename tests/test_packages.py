"""Package import and integration smoke tests.

Verifies that all packages listed in pyscript.json and pyproject.toml
are importable and functional in the local environment.
"""

import importlib.metadata
import sys

import yaml

# ----- YAML Tests -----


def test_yaml_import():
    """Import yaml, test yaml.safe_load on a minimal YAML string."""
    assert yaml.__version__

    result = yaml.safe_load("key: value\nnumber: 42")
    assert result == {"key": "value", "number": 42}


def test_yaml_load_scalar_types():
    """Verify YAML scalar type parsing (int, float, bool, null, string)."""
    yaml_str = """
int_val: 42
float_val: 3.14
bool_true: true
bool_false: false
null_val: null
string_val: hello world
"""
    result = yaml.safe_load(yaml_str)
    assert result["int_val"] == 42
    assert isinstance(result["int_val"], int)
    assert result["float_val"] == 3.14
    assert isinstance(result["float_val"], float)
    assert result["bool_true"] is True
    assert result["bool_false"] is False
    assert result["null_val"] is None
    assert result["string_val"] == "hello world"


def test_yaml_load_list():
    """Load YAML list."""
    result = yaml.safe_load("- a\n- b\n- c\n")
    assert result == ["a", "b", "c"]


def test_yaml_load_complex():
    """Load a multi-document YAML string with nested structures."""
    yaml_str = """
assignments:
  - id: h01
    name: "Assignment 1: Basics"
    criteria_file: criteria/h01.yaml
    enabled: true
    max_points: 24
  - id: h02
    name: "Assignment 2: Data Structures"
    criteria_file: criteria/h02.yaml
    enabled: true
    max_points: 24

criteria:
  general:
    - name: Code Quality
      slug: code_quality
      weight: 4
      main_points:
        - text: "Code follows PEP8"
          sentiment: positive
          sub_points:
            - text: "Proper indentation"
            - text: "Consistent naming"
    - name: Documentation
      slug: documentation
      weight: 3
      main_points:
        - text: "Docstrings present"
          sentiment: positive
        - text: "No docstrings"
          sentiment: negative

grading:
  dimensions:
    - name: code_quality_design
      max_points: 6
      weight: 4
    - name: code_execution_results
      max_points: 6
      weight: 4
    - name: assignment_requirements
      max_points: 6
      weight: 4
    - name: scientific_programming
      max_points: 6
      weight: 4
    - name: creativity
      max_points: 4
      weight: 1
"""

    result = yaml.safe_load(yaml_str)

    # Top-level structure
    assert "assignments" in result
    assert "criteria" in result
    assert "grading" in result

    # Assignments
    assert len(result["assignments"]) == 2
    assert result["assignments"][0]["id"] == "h01"
    assert result["assignments"][0]["enabled"] is True

    # Criteria — nested structure
    assert "general" in result["criteria"]
    assert len(result["criteria"]["general"]) == 2
    code_quality = result["criteria"]["general"][0]
    assert code_quality["slug"] == "code_quality"
    assert len(code_quality["main_points"]) == 1
    assert code_quality["main_points"][0]["sentiment"] == "positive"
    assert len(code_quality["main_points"][0]["sub_points"]) == 2

    # Grading dimensions
    assert len(result["grading"]["dimensions"]) == 5
    total_weight = sum(d["weight"] for d in result["grading"]["dimensions"])
    assert total_weight == 17  # 4+4+4+4+1 = 17 individual weight units


def test_yaml_dump():
    """Verify round-trip: load YAML, dump it, re-load, compare."""
    original = {"key": "value", "nested": {"a": 1, "b": [2, 3]}}
    dumped = yaml.dump(original, default_flow_style=False)
    result = yaml.safe_load(dumped)
    assert result == original


# ----- Package Version Tests -----


def test_package_versions():
    """Print versions of all key packages for documentation."""
    packages = {
        "yaml": "pyyaml",
        "pydantic": "pydantic",
    }

    print("\nPackage version report:")
    for pkg_name in packages.values():
        try:
            version = importlib.metadata.version(pkg_name)
            print(f"  {pkg_name}: {version}")
        except importlib.metadata.PackageNotFoundError:
            print(f"  {pkg_name}: NOT INSTALLED")

    print(f"  Python: {sys.version}")


def test_pyyaml_version():
    """Verify PyYAML version is >= 6.0."""
    version = importlib.metadata.version("pyyaml")
    major = int(version.split(".")[0])
    assert major >= 6, f"PyYAML version {version} is too old (need >= 6.0)"


def test_pydantic_version():
    """Verify Pydantic version is >= 2.0."""
    version = importlib.metadata.version("pydantic")
    major = int(version.split(".")[0])
    assert major >= 2, f"Pydantic version {version} is too old (need >= 2.0)"


# ----- Edge Cases -----


def test_yaml_empty():
    """Load empty YAML string."""
    result = yaml.safe_load("")
    assert result is None


def test_yaml_comments():
    """Verify comments are ignored in YAML."""
    yaml_str = """
# This is a comment
key: value  # inline comment
"""
    result = yaml.safe_load(yaml_str)
    assert result == {"key": "value"}


def test_yaml_unicode():
    """Verify Unicode handling in YAML."""
    yaml_str = """
german_grade: "sehr gut"
japanese: こんにちは
emoji: 🐍
"""
    result = yaml.safe_load(yaml_str)
    assert result["german_grade"] == "sehr gut"
    assert result["japanese"] == "こんにちは"
    assert result["emoji"] == "🐍"
