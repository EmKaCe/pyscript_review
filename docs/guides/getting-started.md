# Getting Started with SciPro Review

This guide helps you set up and run the SciPro Review project locally.

## Prerequisites

- Python 3.13
- `uv` (Python package installer and manager)

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   uv sync
   ```

## Running the Application

The app is a PyScript SPA and can be served statically. Use the project task:
```bash
uv run task serve
```
Then open the provided URL in your browser.

## Quality Control

You can run the project's quality checks using the following commands:

- **Tests**: `uv run task test`
- **Linting/Typing**: `uv run task check`
- **Full CI Suite**: `uv run task ci`

## Project Structure

- `src/`: Source code for the application.
  - `models/`: Pydantic models and domain data structures.
  - `services/`: Business logic for grading and criteria loading.
  - `browser/`: JavaScript interop and browser-specific APIs.
  - `state.py`: Reactive state management.
- `docs/`: Sphinx documentation.
- `tests/`: Pytest suite.
- `static/`: Static assets (CS, CSS, wheels).
