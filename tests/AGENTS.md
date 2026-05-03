# tests — TEST SUITE CONVENTIONS

## OVERVIEW

pytest suite with 14 modules, 4483 lines. Per-module fixtures, in-memory backends, no mocking.

## STRUCTURE

```
tests/
├── test_state.py             # 547L — ReviewState, undo/redo, serialization
├── test_models.py            # 427L — Pydantic model creation, serialization
├── test_criteria_loader.py   # 725L — YAML parsing via tmp_path
├── test_browser_storage.py   # 656L — MemoryStorage CRUD, async
├── test_text_generator.py    # 462L — output format, sentiment grouping
├── test_grade_calculator.py  # 279L — grade boundaries
├── test_grade_result_near_fence.py # 280L — near-fence field verification
├── test_grading_config.py    # 113L — DEFAULT_GRADING_CONFIG validation
├── test_default_state.py     # 135L — DEFAULT_STATE keys, types
├── test_semester.py          # 183L — semester parsing/display
├── test_grade_colors.py      # 110L — color mapping
├── test_category_progress.py # 141L — ReviewState category progress
├── test_timer_manager.py     # 89L — no-op browser shim
├── test_packages.py          # 203L — smoke tests
└── test_pyodide_smoke.py     # 133L — Pydantic v2 fallback record
```

## CONVENTIONS

- **No conftest**: every fixture is per-module. Also uses `_make_*` factory helpers instead of fixtures.
- **No mocking**: in-memory backends (`MemoryStorage`) + no-op degradation (`TimerManager` outside browser).
- **Bare `assert`**: ruff `S101` suppressed for tests.
- **No parametrize**: all cases as separate methods or repeated blocks (even repetitive boundary tests).
- **No markers**: `unit`, `integration`, `slow` defined but never used.
- **Async**: only `test_browser_storage.py`; `asyncio_mode=auto` in config.
- **Section dividers**: `# --- section ---` in larger modules.
- **Type hints**: `-> None` on all test methods; Google-style docstrings on helpers.
- **File I/O**: `tmp_path` fixture for YAML in `test_criteria_loader.py`.
- **State registry gate**: `test_default_state.py` dedicated to verifying DEFAULT_STATE completeness.

## ANTI-PATTERNS

- Do NOT add conftest — keep fixtures per-module
- Do NOT use unittest.mock — use in-memory backends instead
- Do NOT parametrize — separate methods preferred (project convention)
- No `# noqa: SIM117` needed — globally ignored
