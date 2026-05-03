# YAML Content Management

This page explains how assignments and rubric criteria are defined, loaded, and managed. Understanding this is essential for professors and TAs who need to add or modify rubric content.

## File Layout

Assignments and criteria are served as static files in the `static/data/` directory:

```text
static/data/
├── assignments.yaml          # Master registry of all assignments
└── criteria/
    ├── general.yaml          # Shared rubric (loaded for every assignment)
    ├── user_function.yaml    # Assignment-specific rubric
    ├── pandas.yaml
    └── ...                   # Individual YAML per assignment
```

## Data Models

The structure of the YAML files is defined by Pydantic models in `src/models/criteria.py`:

```python
class SubPoint(BaseModel):
    text: str                # Display text for the checkbox
    comment: bool = False    # Show a custom comment textarea when selected
    point_deduction: bool = False  # Show a numeric deduction input

class MainPoint(BaseModel):
    main_point: str          # Heading for a group of sub-points
    sub_points: list[SubPoint]

class Category(BaseModel):
    title: str               # Human-readable category name
    additional_notes: bool = True
    positive: list[MainPoint]
    neutral: list[MainPoint]
    negative: list[MainPoint]

class AssignmentConfig(BaseModel):
    id: str                  # Unique identifier (kebab-case)
    title: str               # Display title in the UI
    enabled: bool = True     # Visibility flag
    criteria_files: list[str] # List of paths to criteria YAMLs
```

## Configuring Assignments

The `assignments.yaml` file acts as the registry. To add a new assignment, create an entry:

```yaml
- id: numpy_arrays
  title: "NumPy Array Basics"
  enabled: true
  criteria_files:
    - data/criteria/numpy_arrays.yaml
```

## Criteria Structure

Each criteria YAML file defines categories with three sentiment directions:

- **`positive`**: Praise-worthy items.
- **`neutral`**: Suggestions for improvement.
- **`negative`**: Deductions and errors.

Example:

```yaml
general:
  codingStyle:
    title: "Coding Style"
    additional_notes: true
    positive:
      - main_point: "Naming"
        sub_points:
          - text: "Excellent use of snake_case for all variables"
    negative:
      - main_point: "Formatting"
        sub_points:
          - text: "Hardcoded paths detected"
            point_deduction: true
```

## Merge Logic

When an assignment is selected, the `CriteriaLoader` service:
1. Loads `general.yaml` (providing baseline criteria like Code Formatting).
2. Loads all files listed in `criteria_files`.
3. Merges the categories. If a category key exists in both, the assignment-specific one takes precedence.

---

For technical details on how these models are used in grading, see [Architecture](./architecture.md).
hitecture.md). For developer setup, see [Contributing](./contributing.md).