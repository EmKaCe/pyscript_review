# pyscript_review PROJECT KNOWLEDGE BASE

**Generated:** 2026-05-03

## OVERVIEW

pyscript_review is a modern peer-review and grading system built as a client-side SPA using PyScript, PuePy, and Basecoat CSS. It implements the German university grading scale (1.0-5.0) for Python programming courses.

## RUNTIME VERSIONS
| Technology    | Version |
|---------------|---------|
| PuePy         | 0.6.5   |
| PyScript      | 2026.3.1|
| Basecoat CSS  | 0.3.11  |
| Tailwind CSS  | v4 CDN  |
| Python        | 3.13    |

## STRUCTURE
```
pyscript_review/
├── src/
│   ├── app.py              # Application(), Router, page registration
│   ├── state.py            # DEFAULT_STATE, ReactiveDict, session helpers
│   ├── main.py             # PyScript entry point, imports app
│   ├── models/             # Pydantic domain models (Criteria, Rubric, etc.)
│   ├── components/
│   │   ├── atomic/         # Basecoat-powered primitives
│   │   └── feature/        # Composed UI sections
│   ├── services/           # Business logic (grade calculation, storage)
│   ├── pages/              # Page-level components
│   └── browser/            # JS interop shims (IndexedDB, BasecoatBridge)
├── tests/
│   └── unit/               # pytest suite
├── static/
│   └── puepy-0.6.5-py3-none-any.whl
├── pyscript.json           # File mappings, packages, js_modules
├── pyproject.toml          # ruff, pyright, pytest config
└── taskfile.yml             # Automation commands
```

## SPECIALISTS

| Specialist            | Responsibility                                                                                                                                                                                                                                                                                                                                                             |
|-----------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PuePy/PyScript Integrator | Component lifecycle, state reactivity (Two-State Model), routing (LINK_MODE_HASH), hooks, events, refs, watchers, FFI (create_proxy), bind= leak fix, pyscript.json config, JS interop, mutate() for lists/dicts                                                                                                                                                                       |
| Basecoat/UI Architect | Component mapping (shadcn → Basecoat), CSS classes (.btn, .card, .input, etc.), JS component init (BasecoatBridge pattern after PuePy redraws), dark mode (.dark class), Basecoat components vs pure CSS                                                                                                                                                                           |
| Domain Teacher        | German 1.0-5.0 grading scale (11-step boundaries), rubric categories (7 general + per-assignment), checkbox sentiments (positive/neutral/negative), weighted dimensions (5 dims, total weight 100), text generation from selections                                                                                                                                          |
| Python Inspector      | ruff (line-length=100, E/W/F/I/N/UP/B/C4/SIM/ARG, ignore E501/N812), pyright (basic, pythonVersion=3.13), pytest (testpaths=tests), Google-style docstrings                                                                                                                                                                                                  |

## FILE MAP

| What                         | Location                                    | Notes                                  |
|------------------------------|---------------------------------------------|----------------------------------------|
| PyScript entry point         | `src/main.py`                               | Bootstraps app, adds `/` to sys.path   |
| Application root             | `src/app.py`                                | SciProReviewApp, Router, shortcuts      |
| Reactive state               | `src/state.py`                              | `DEFAULT_STATE` must contain all app keys, `ReviewState` wrapper |
| Domain models                | `src/models/`                               | Pydantic models with `Field(description=...)` |
| Atomic components            | `src/components/atomic/`                    | Basecoat-based primitives, 15 components |
| Feature components           | `src/components/feature/`                   | Composed UI sections, data flow heavy   |
| Services                     | `src/services/`                             | Grade calc, text gen, criteria loader   |
| Pages                        | `src/pages/`                                | Router pages: home, review, settings, about |
| JS interop                   | `src/browser/`                              | IndexedDB, BasecoatBridge, theme, files  |
| Test suite                   | `tests/`                                    | 14 modules, 4483 lines, pytest + asyncio |
| Build scripts                | `scripts/`                                  | `download_wheels.py` (custom PyPI fetcher) |
| PuePy documentation          | `../meta/extra/puepy/docs/`                  | Architecture, component, state docs       |
| PyScript documentation       | `../meta/extra/pyscript-docs/`              | Runtime and configuration guides       |
| Basecoat documentation      | `../meta/extra/basecoat/docs/`               | CSS framework and JS components         |

## CONVENTIONS

- **Naming:** kebab-case files, `snake_case` Python, `camelCase` JS
- **Line length:** 100 chars (ruff enforced)
- **Quotes:** double quotes
- **Python style:** Google docstrings, type hints required, Pydantic with `Field(description=...)`
- **Components:** `atomic/` primitives, `feature/` composed; `@t.component()` decorator
- **No build step:** Basecoat/Tailwind via CDN, PyScript via CDN
- **Tests:** per-module fixtures (no conftest), bare `assert`, in-memory backends instead of mocking, `asyncio_mode=auto`, section dividers

## CRITICAL ARCHITECTURE RULES

### PuePy Two-State Model (MUST follow)
Every PuePy `Page` and `Component` has TWO state contexts:
1. **`self.state`** — local `ReactiveDict(self.initial({}))`. Page-scoped, ephemeral. Use for UI-only state like active tabs, accordion open/close.
2. **`self.application.state`** — shared app-wide `ReactiveDict`. Persistent across pages. Use for ALL business data (mode, session, criteria, grades).
**Rule:** If data survives navigation or is shared $\rightarrow$ `self.application.state`. If UI-local $\rightarrow$ `self.state`.

### PuePy `bind` Leak Fix (MUST apply)
To prevent `KeyError` during redraws for components using `bind=...`:
```python
class SciProInput(Component):
    def __init__(self, *args, **kwargs):
        self._bind_key = kwargs.pop("bind", "")
        super().__init__(*args, **kwargs)

    def _handle_bind(self, kwargs):
        kwargs.pop("bind", None)
        self.bind = None
```
The component must then use `self._bind_key` with `self.application.state`.

### Component Instantiation — `t.*()` Builder ONLY (CRITICAL)

**This is the #1 source of runtime bugs. Direct class instantiation breaks PuePy's lifecycle.**

PuePy's official docs (reference/component.md) state:
> "Components should not be created directly. In your `populate()` method, call `t.tag_name()` to create a component. There's no reason an application developer should directly instantiate a component instance and doing so is not supported."

**How it works:**
1. `@t.component()` registers the class with the `t` Builder, mapping it to a lowercase method.
2. The `component_name` class attribute controls the method name on `t` (defaults to kebab-case of class name).
3. `t.component_name()` calls `Builder.generate_tag()`, which provides the required `ref`, `origin`, and `page` arguments automatically.
4. Direct `ComponentClass()` bypasses the Builder — missing required args cause `Tag.__init__() missing 1 required positional argument: 'ref'`.

**Mandatory pattern:**

```python
# 1. Define and register the component
@t.component()
class SciProCard(Component):
    component_name = "sci-pro-card"  # → t.sci_pro_card()
    # ...

# 2. Use it in populate() via the Builder
class ReviewPage(Page):
    def populate(self):
        with t.sci_pro_card(variant="outlined"):
            t.p("Content inside the card")
```

**BANNED — will crash at runtime:**
```python
# ❌ NEVER do this — missing ref/origin/page causes Tag.__init__() crash
from src.components.atomic.card import SciProCard
SciProCard(variant="outlined")

# ❌ NEVER import component classes into pages to call them directly
from src.components.atomic.input import SciProInput  # remove this import
SciProInput(bind="score")  # crashes with Tag.__init__() error
```

**Naming convention:**
| Class Name              | `component_name`       | Builder Call              |
|-------------------------|------------------------|---------------------------|
| `SciProCard`            | `"sci-pro-card"`       | `t.sci_pro_card()`        |
| `SciProButton`          | `"sci-pro-button"`     | `t.sci_pro_button()`      |
| `SciProInput`           | `"sci-pro-input"`      | `t.sci_pro_input()`       |
| `SciProGradeSlider`     | `"sci-pro-grade-slider"` | `t.sci_pro_grade_slider()` |

**Rule:** Pages must NEVER import component classes from `components/atomic/` or `components/feature/`. The `t` Builder is the sole entry point for component instantiation.

### Component Authoring (Slots, Props, Events)

From PuePy docs (guide/in-depth-components.md):

- **Props** — define accepted data as a list of strings or `Prop` instances:
  ```python
  class SciProCard(Component):
      props = ["variant", Prop("size", "Card size", str, "md")]
  ```
- **Attributes** — kwargs that don't match any prop become HTML attributes on the rendered element.
- **Events** — use `self.trigger_event("name", detail={...})` in components; consume with `on_name=self.handler` in the parent.
- **Slots** — define with `self.insert_slot("slot-name")` in `populate()`; consume with `component.slot("slot-name")`:
  ```python
  # In component:
  def populate(self):
      with t.div():
          self.insert_slot("header")
          self.insert_slot()  # default slot

  # In parent:
  with t.sci_pro_card() as card:
      with card.slot("header"):
          t.h3("Title")
      with card.slot():
          t.p("Body content")
  ```
- **Parent/Child** — `self.page` (Page), `self.origin` (creating component), `self.parent` (direct DOM parent). Do NOT modify these.

### General PuePy Rules
- **`Component.update()` does NOT exist:** Use `self.page.redraw_tag(self)` or mutate a reactive key.
- **Mutable Defaults:** Never use `list` or `dict` as class-level attributes. Initialize in `bind()`.
- **Reactive Mutations:** Use `mutate()` method for in-place list/dict changes to trigger reactivity.
- **Watchers:** `on_<key>_change` methods are auto-registered watchers.
- **DOM Preservation:** `ref="name"` preserves DOM elements across redraws.
- **Redraw Triggers:** Add keys to `redraw_on_state_changes` (local) or `redraw_on_app_state_changes` (global) to auto-redraw when those keys change.

### PyScript & JS Interop
- **`create_proxy`:** Use `pyodide.ffi.create_proxy` for ALL raw JS event listeners (e.g., `window.addEventListener`).
- **`pyscript.json`:** All `src/*.py` files must be mapped in the `files` section.
- **BasecoatBridge:** Call `window.basecoat.initAll()` in `on_ready` after page transitions to re-initialize Basecoat JS components. MUST be called on every page.
- **Persistence:** Use IndexedDB via JS interop for reviews; `pyscript.storage` (localStorage) has a 5MB limit and is insufficient.
- **Icons:** Use Lucide static icons via CSS (jsdelivr) to keep raw SVGs and HTML to a minimum.
- **Wheels:** Required `.whl` files in `static/` ARE tracked in Git as they are required for the PyScript runtime and CI testing.

## ANTI-PATTERNS

- Do NOT instantiate components directly — `SciProCard()` crashes with `Tag.__init__() missing 'ref'`. Use `t.sci_pro_card()` Builder.
- Do NOT import component classes into pages — the `t` Builder is the sole entry point for component creation.
- Do NOT add React/Vue/Next.js/shadcn CLI — this is a PyScript/PuePy app.
- Do NOT run `npx shadcn add` — use Basecoat CSS components.
- Do NOT use `pyscript.storage` for review data (5MB limit) — use IndexedDB.
- Do NOT write business logic in JS — use Python in `src/` and JS only for browser shims in `src/browser/`.
- Do NOT pass `bind=` to components without the `_handle_bind` override.
- Do NOT rename `from puepy import t`.
- Do NOT use `self.state.get("mode")` for app-wide data.
- Do NOT call `self.update()`.
- Do NOT use bare `except:`.
- Do NOT use class-level mutable defaults.
- Do NOT add Python keys to `self.application.state` that are not in `DEFAULT_STATE`.
- Do NOT use `pyscript.json` with fewer than all `src/*.py` files — missing files cause `ModuleNotFoundError`.
- Do NOT rely on `taskfile.yml` (Go Task config) — it's dead config; the real task runner is taskipy from `pyproject.toml`.
- Do NOT use `pyscript.json` with `debug: true` in production — exposes verbose runtime info.
- Do NOT add `# noqa: SIM117` — SIM117 is already globally ignored in pyproject.toml.
- Do NOT put imports inside methods — use top-level imports (review_page.py has 2 method-level imports).

## COMMANDS

```bash
task check    # ruff check + pyright
task test     # pytest -v
task ci       # check + test
task format    # ruff format
task serve    # local http server
task docs     # generate/open docs
task download-wheels # fetch puepy/etc wheels
```
