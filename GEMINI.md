# pyscript_review — Gemini Project Instructions

**Project**: PuePy/PyScript SPA with Basecoat CSS for peer review. Client-side only. German 1.0-5.0 grading scale.

See `AGENTS.md` for the complete project knowledge base. Below are the 12 most critical rules every agent MUST follow.

---

## 1. Component Instantiation — `t.*()` Builder ONLY

**This is the #1 source of runtime bugs.** PuePy's official docs explicitly state: "Components should not be created directly."

- **REQUIRED**: Use `t.component_name()` to instantiate components in `populate()`. The Builder calls `generate_tag()` which provides required `ref`, `origin`, `page` args.
- **BANNED**: `SciProCard(variant="outlined")` — direct class instantiation crashes with `Tag.__init__() missing 1 required positional argument: 'ref'`.
- **BANNED**: Importing component classes into pages. The `t` Builder is the sole entry point.

```python
# ✅ CORRECT — via Builder
with t.sci_pro_card(variant="outlined"):
    t.p("Content")

# ❌ WRONG — direct class call (CRASHES)
from src.components.atomic.card import SciProCard
SciProCard(variant="outlined")
```

Naming convention: class `SciProCard` → `component_name = "sci-pro-card"` → `t.sci_pro_card()`.

## 2. PuePy Two-State Model

Every `Page`/`Component` has TWO state contexts:
- **`self.state`** — local `ReactiveDict`. For UI-only: active tabs, accordion open/close, drag flags.
- **`self.application.state`** — shared app-wide `ReactiveDict`. For ALL business data: mode, session, criteria, form fields, grades.

**Rule**: If data survives navigation or is shared between components → `self.application.state`. If UI-local → `self.state`. `self.state.get("key")` does NOT fall through to `self.application.state`.

## 3. `bind=` Leak Fix (MUST apply)

Every component receiving `bind=...` MUST save the key in `__init__` and override `_handle_bind`:

```python
def __init__(self, *args, **kwargs):
    self._bind_key = kwargs.pop("bind", "")
    super().__init__(*args, **kwargs)

def _handle_bind(self, kwargs):
    kwargs.pop("bind", None)
    self.bind = None
```

Required on: `SciProInput`, `SciProSelect`, `SciProTextarea` (and any future bind-using component).

## 4. `Component.update()` Does NOT Exist

PuePy `Component` has no `update()`. Redraw via:
- Mutating a key in `redraw_on_state_changes` / `redraw_on_app_state_changes` (auto-triggers)
- Manual: `self.page.redraw_tag(self)`

Never call `self.update()`. It will fail silently.

## 5. `create_proxy` for Raw JS Event Listeners

Python callbacks passed to `window.addEventListener` MUST be wrapped:

```python
from pyodide.ffi import create_proxy
self._proxy = create_proxy(self._on_keydown)
window.addEventListener("keydown", self._proxy)
```

PuePy's `on_click`/`on_change` kwargs do NOT need this — PuePy wraps internally.

## 6. No Class-Level Mutable Defaults

```python
# BAD — shared across instances:
_saved_sessions: list = []

# GOOD — immutable or None sentinel:
_loading: bool = True
_saved_sessions: list | None = None  # init in bind()
```

## 7. Basecoat CSS, Not shadcn

This is a PyScript/PuePy app. Use Basecoat CSS classes (`.btn`, `.card`, `.input`, `.table`, etc.). Do NOT add React/shadcn/Next.js. Do NOT run `npx shadcn add`. Components are Python `@t.component()` classes, not TSX.

## 8. BasecoatBridge After Page Transitions

After PuePy redraws or navigates to a new page, call:

```python
import js
js.window.basecoat.initAll()
```

This re-initializes Basecoat JS components (modals, dropdowns, tabs) that were destroyed during the redraw. Implement in page `on_ready()`.

## 9. IndexedDB, Not localStorage

localStorage has a 5MB limit (via `pyscript.storage`). Use IndexedDB via JS interop (`src/browser/`) for review data. localStorage is acceptable only for small config values.

## 10. All State Keys in `DEFAULT_STATE`

Every key used with `self.application.state` MUST be declared in `DEFAULT_STATE` in `src/state.py`. Adding keys at runtime without declaration will cause reactivity issues and undefined behavior.

## 11. Component Slots, Props, and Events

- **Props**: Define with `props = ["variant", Prop("size", "Card size", str, "md")]`.
- **Events**: Emit with `self.trigger_event("name", detail={...})`. Consume with `on_name=self.handler`.
- **Slots**: Define with `self.insert_slot("slot-name")`. Consume with `component.slot("slot-name")`. **Never call `t.slot()`** — use `card.slot()` on the component instance.
- **Parent/Child**: `self.page` (Page), `self.origin` (creating Component), `self.parent` (direct DOM parent). Do NOT modify these.

## 12. Code Style: ruff + pyright Enforced

- Line length: 100 chars
- Double quotes for strings
- Google-style docstrings with `@param`/`@returns`
- Type hints required on all function signatures
- Pydantic models use `Field(description=...)`
- `task check` runs: `ruff check` + `pyright`
- `task format` runs: `ruff format`
- `task test` runs: `pytest -v`
- `task ci` runs: check + test

## 13. Lucide Icons via CSS

To keep raw SVG and raw HTML to a minimum, use Lucide static icons via CSS (jsdelivr) and apply them using standard CSS classes (`<i class="i-lucide-name"></i>`).
