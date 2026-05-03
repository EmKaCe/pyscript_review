# Architecture Guide

This document explains the architectural patterns used in SciPro Review.

## PuePy Two-State Model

The application uses a dual-state architecture to separate UI-local state from business data.

### `self.state` (Local State)
- **Scope**: Component-level or Page-level.
- **Lifetime**: Ephemeral; lost on navigation or component destruction.
- **Use Case**: UI flags, active tab indices, accordion states, drag-and-drop indicators.

### `self.application.state` (Global State)
- **Scope**: Application-wide.
- **Lifetime**: Persistent across navigation and page transitions.
- **Use Case**: User session, grading criteria, form inputs, final grades, and shared configuration.

**Rule**: If data must survive navigation or is shared between different components, it MUST reside in `self.application.state`.

## Component Lifecycle

PuePy components follow a strict initialization sequence:

1. `__init__()`: Basic object instantiation.
2. `_configure(kwargs)`: Processing of component properties (props).
3. `_handle_bind(kwargs)`: Binding keys are processed here.
4. `_handle_attrs(kwargs)`: HTML attributes are set.
5. `self.state = ReactiveDict(self.initial())`: Local state is initialized.
6. `bind()`: Logic for connecting state to UI.
7. `populate()`: Final data population before render.
8. `on_ready()`: Component is fully mounted in the DOM.

## Component Instantiation

**PuePy's official documentation explicitly states**: "Components should not be created directly. In your `populate()` method, call `t.tag_name()` to create a component. There's no reason an application developer should directly instantiate a component instance and doing so is not supported."

### How the Builder Works

The `@t.component()` decorator registers a class with PuePy's `t` Builder object. When you call `t.component_name()` in `populate()`, it invokes `Builder.generate_tag()`, which automatically provides the required `ref`, `origin`, and `page` arguments that the component's `__init__` expects.

Direct class instantiation (e.g., `SciProCard(...)`) bypasses the Builder and results in a `Tag.__init__() missing 1 required positional argument: 'ref'` runtime error.

### Correct Pattern

```python
# 1. Define and register the component
@t.component()
class SciProCard(Component):
    component_name = "sci-pro-card"  # → t.sci_pro_card()
    props = ["variant"]

    def populate(self):
        with t.div(classes=["card", f"card-{self.variant}"]):
            self.insert_slot()  # default slot

# 2. Use it in a page via the Builder
class ReviewPage(Page):
    def populate(self):
        with t.sci_pro_card(variant="outlined"):
            t.p("Content inside the card")
```

### Naming Convention

| Class Name           | `component_name`         | Builder Call                |
|----------------------|--------------------------|-----------------------------|
| `SciProCard`         | `"sci-pro-card"`         | `t.sci_pro_card()`          |
| `SciProButton`       | `"sci-pro-button"`       | `t.sci_pro_button()`        |
| `SciProInput`        | `"sci-pro-input"`        | `t.sci_pro_input()`         |
| `SciProGradeSlider`  | `"sci-pro-grade-slider"` | `t.sci_pro_grade_slider()`  |

### Anti-Pattern: Direct Instantiation

```python
# ❌ WRONG — crashes with Tag.__init__() missing 'ref'
from src.components.atomic.card import SciProCard
SciProCard(variant="outlined")

# ✅ CORRECT — via Builder
with t.sci_pro_card(variant="outlined"):
    t.p("Content")
```

Pages must NEVER import component classes. The `t` Builder is the sole entry point for creating component instances.

## Component Authoring

### Props

Define accepted data as a list of strings or `Prop` instances:

```python
class SciProCard(Component):
    props = ["variant", Prop("size", "Card size", str, "md")]
```

Kwargs that don't match any prop become HTML attributes on the rendered element.

### Events

Emit custom events with `self.trigger_event("name", detail={...})`. Consume with `on_name=self.handler`:

```python
# In component:
def some_method(self):
    self.trigger_event("greeting", detail={"message": "Hello"})

# In parent:
class MyPage(Page):
    def populate(self):
        t.my_component(on_greeting=self.on_greeting_sent)

    def on_greeting_sent(self, event):
        print(event.detail.get("message"))
```

### Slots

Define slots with `self.insert_slot()` in `populate()`. Consume with `component.slot()`:

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

**Important**: Use `card.slot("header")`, NOT `t.slot("header")` or `self.slot("header")`.

### Parent/Child Relationships

- `self.page` — the Page instance responsible for rendering
- `self.origin` — the Component that created this one in its `populate()`
- `self.parent` — direct DOM parent (a `Tag` instance, not necessarily a Component)

Do NOT modify these attributes.

## Browser Interop Pattern

Since the app runs in PyScript (Pyodide), it interacts with the browser's JavaScript environment. To support both browser execution and `pytest` execution, a dual-mode import pattern is used:

```python
try:
    from js import window, document, localStorage
except ImportError:
    from unittest.mock import MagicMock
    window = MagicMock()
    document = MagicMock()
    localStorage = MagicMock()
```

## Core System Components

### Basecoat Bridge
The `BasecoatBridge` provides a unified interface to the Basecoat UI framework. It is initialized via `init_basecoat()` and manages global UI themes and layout behaviors.

### IndexedDB Persistence
The `BrowserStorage` service handles the persistence of session data into IndexedDB, ensuring that review progress is not lost on page refresh.
