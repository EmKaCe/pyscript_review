# src/components/atomic — BASECOAT PRIMITIVES

## OVERVIEW

15 Basecoat-powered primitive components wrapping CSS classes. Each is a `@t.component()` class with props, slots, and events.

## COMPONENT LIST

| File | Builder Call | Key Props |
|------|-------------|-----------|
| `badge.py` | `t.sci_pro_badge()` | `variant`, `label` |
| `button.py` | `t.sci_pro_button()` | `variant`, `size`, `disabled` |
| `card.py` | `t.sci_pro_card()` / header / title / description / content / footer | `variant` |
| `checkbox.py` | `t.sci_pro_checkbox()` | `checked`, `label`, `on_change` |
| `icon.py` | `t.sci_pro_icon()` | `name`, `size` |
| `input.py` | `t.sci_pro_input()` | `bind`, `placeholder`, `type` (needs bind leak fix) |
| `progress_bar.py` | `t.sci_progress_bar()` | `value`, `max`, `label` |
| `select.py` | `t.sci_pro_select()` | `bind`, `options` (needs bind leak fix) |
| `separator.py` | `t.sci_pro_separator()` | `orientation` |
| `skeleton.py` | `t.sci_pro_skeleton()` | `variant`, `lines` |
| `slider.py` | `t.sci_pro_slider()` | `label`, `min`, `max`, `step`, `value`, `on_change` |
| `table.py` | `t.sci_pro_table()` | `headers`, `rows` |
| `textarea.py` | `t.sci_pro_textarea()` | `bind`, `rows` (needs bind leak fix) |
| `tooltip.py` | `t.sci_pro_tooltip()` | `content`, `position` |

## CONVENTIONS

- **Props**: `props = ["variant", Prop("size", "...", str, "md")]` (list of strings or `Prop` instances).
- **Slots**: Define with `self.insert_slot("slot-name")`; consume via `component.slot("slot-name")`, NOT `t.slot()`.
- **Events**: `self.trigger_event("name", detail={...})`; consume with `on_name=self.handler`.
- **bind leak fix** (input/select/textarea): `self._bind_key = kwargs.pop("bind", "")` in `__init__`, `_handle_bind` strips bind from kwargs.
- **component_name**: MUST be set explicitly (e.g., `component_name = "sci-pro-button"`). Some components omit it and rely on PuePy default kebab-case conversion — inconsistent.

## ANTI-PATTERNS

- Never instantiate directly — `SciProCard()` crashes. Use `t.sci_pro_card()`.
- Never import component classes into pages — use `t` Builder only.
- `SciProInput`/`SciProSelect`/`SciProTextarea` lack explicit `component_name` — add if PuePy default conversion breaks.
