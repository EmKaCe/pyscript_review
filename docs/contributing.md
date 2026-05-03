# Contributing to SciPro Review

This guide covers everything a new developer needs to set up the project, follow the code style, run tests, and submit changes. Read the [architecture overview](./architecture.md) first to understand the system design.

## 1. Development Setup

### Prerequisites

- **Python 3.13** or higher.
- **`uv`**: Fast Python package and project manager.
- **Node.js**: Required only for local development of certain JS shims (optional).

### Installation

Clone the repository and sync dependencies using `uv`:

```bash
uv sync
```

This will create a virtual environment and install all dependencies, including PuePy (from the local wheel in `static/`).

### Development Server

Start the project's development server:

```bash
uv run task dev
```

The server runs on `http://localhost:8080`. Open this URL in your browser. Since this is a PyScript app, changes to `.py` files are picked up on page reload as the browser re-fetches and re-runs the code.

## 2. Code Style

The project enforces a strict Python style to ensure maintainability.

### General Rules

- **Line Length**: 100 characters (enforced by ruff).
- **Quotes**: Double quotes for all string literals.
- **Type Hints**: Required for all function signatures and public class attributes.
- **Naming**: `snake_case` for Python files, variables, and functions. `PascalCase` for classes.

### Component Authoring (PuePy)

- **Builder Pattern**: NEVER instantiate components directly (e.g., `SciProCard()`). Always use the `t.*()` builder (e.g., `t.sci_pro_card()`).
- **Two-State Model**: Use `self.application.state` for data that survives navigation and `self.state` for ephemeral UI-only data.
- **Slots**: Define slots using `self.insert_slot("name")` and consume them via `component.slot("name")`.

### Documentation (Google Style)

Use Google-style docstrings for all functions and classes:

```python
def calculate_grade(score: float, max_points: float) -> str:
    """Calculates the German decimal grade from a raw score.
    
    Args:
        score: The student's raw score.
        max_points: The maximum possible points.
        
    Returns:
        A string representing the German grade (e.g., "1.3").
    """
    ...
```

## 3. Quality Control & Testing

Use the `task` commands to run quality checks:

- **Linting & Type Checking**: `uv run task check` (runs `ruff` and `pyright`).
- **Formatting**: `uv run task format` (runs `ruff format`).
- **Testing**: `uv run task test` (runs `pytest`).

### Test Suite

Tests are located in `tests/` and use `pytest`. We prioritize integration tests that exercise the business logic (grading, criteria loading) in an environment that mimics the browser runtime.

## 4. Project Structure

- `src/`: Python source code.
  - `components/`: PuePy components (atomic and feature).
  - `pages/`: Page-level components.
  - `services/`: Core business logic (grading, text generation).
  - `models/`: Pydantic domain models.
  - `browser/`: JS interop shims.
- `static/`: Static assets and PuePy wheels.
- `docs/`: Sphinx documentation.
- `tests/`: Test suite.

## 5. Commit Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semi-colons, etc.
- `refactor`: Code change that neither fixes a bug nor adds a feature
- `test`: Adding missing tests or correcting existing tests
- `chore`: Updating build tasks, package manager configs, etc.

Example: `feat: add student mode toggle to settings page`

---

- [User Guide](./user-guide.md)
- [Architecture](./architecture.md)
- [YAML Content](./yaml-content.md)
