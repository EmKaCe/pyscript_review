# PyScript Review

A client-side single-page application for peer review and grading in Python programming courses, built with [PyScript](https://pyscript.net/), [PuePy](https://puepy.dev/), and [Basecoat CSS](https://basecoatui.com/). Implements the German university grading scale (1.0–5.0) with rubric-based criteria, weighted scoring, and evaluation text generation.

## Tech Stack

| Technology   | Version  |
|-------------|----------|
| PuePy       | 0.6.5    |
| PyScript    | 2026.3.1 |
| Basecoat CSS | 0.3.11  |
| Tailwind CSS | v4 CDN  |
| Python      | 3.13     |

## Project Structure

```
pyscript_review/
├── src/
│   ├── app.py              # Application(), Router, page registration
│   ├── state.py            # DEFAULT_STATE, ReactiveDict, session helpers
│   ├── main.py             # PyScript entry point
│   ├── models/             # Pydantic domain models (Criteria, Rubric, etc.)
│   ├── components/
│   │   ├── atomic/         # Basecoat-powered primitives (15 components)
│   │   └── feature/        # Composed UI sections
│   ├── services/           # Business logic (grade calculation, storage, text gen)
│   ├── pages/              # Page-level components (home, review, settings, about)
│   └── browser/            # JS interop shims (IndexedDB, BasecoatBridge, files)
├── tests/                  # pytest suite (349+ tests)
├── static/                 # Wheel dependencies for PyScript runtime
├── pyscript.json           # File mappings, packages, js_modules
├── pyproject.toml           # ruff, pyright, pytest, taskipy config
└── docs/                    # Sphinx documentation source
```

## Development

```bash
# Install dependencies
uv sync

# Run linter and type checker
task check

# Run tests
task test

# Full CI pipeline (lint + type check + test + docs)
task ci

# Start development server (downloads wheels, builds docs, serves on :8080)
task dev

# Format code
task format
```

## Architecture

- **Two-State Model**: `self.state` for UI-local data (active tabs, accordion state); `self.application.state` for shared business data (mode, session, criteria, grades).
- **Component Instantiation**: Always use `t.sci_pro_*()` builder — never direct class instantiation.
- **Persistence**: IndexedDB for reviews (via JS interop in `src/browser/`); localStorage for small config only.
- **No Backend**: Entirely client-side. All logic runs in the browser via PyScript/WASM.

## License

Private project. All rights reserved.