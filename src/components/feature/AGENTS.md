# src/components/feature — COMPOSED UI SECTIONS

## OVERVIEW

15 composed UI components with heavy data flow. Connect `self.application.state` → rendering. 2231 lines.

## COMPONENT LIST

| File | Builder Call | Role |
|------|-------------|------|
| `category_panel.py` | `t.sci_pro_category_panel()` | Renders rubric category with checkboxes, notes |
| `dropdown.py` | `t.sci_pro_dropdown_menu()` | Dropdown menu trigger + content |
| `evaluation_output.py` | `t.sci_pro_evaluation_output()` | Generated text display + copy |
| `grading_sidebar.py` | `t.sci_pro_grading_sidebar()` | Grade slider + dimension inputs |
| `header.py` | `t.sci_pro_header()` | Top nav bar with mode toggle |
| `import_review_card.py` | `t.sci_pro_import_review_card()` | Import review from file |
| `load_review_card.py` | `t.sci_pro_load_review_card()` | Browse/load saved reviews |
| `mode_toggle.py` | `t.sci_pro_mode_toggle()` | Switch between home/review/settings |
| `new_review_card.py` | `t.sci_pro_new_review_card()` | Create new review session |
| `popover.py` | `t.sci_pro_popover()` | Popover overlay |
| `review_footer.py` | `t.sci_pro_review_footer()` | Generate/Copy/Export actions |
| `sidebar_sheet.py` | `t.sci_pro_sidebar_sheet()` | Slide-out sidebar for review list |
| `tabs.py` | `t.sci_pro_tabs()` | Tabbed interface |
| `toast.py` | `t.sci_pro_toaster()` + `show_toast()` | Toast notification system |

## CONVENTIONS

- **Two-State Model**: feature components read FROM `self.application.state` for business data, write via `ReviewState` methods.
- **No direct state mutation**: use `review_state.toggle_checkbox()`, `review_state.set_comment()`, etc.
- **Tree**: Pages create feature components → feature components create atomic components. Never the reverse.
- **Props for config only**: pass assignment_id, category data as props; actual state comes from app state.

## ANTI-PATTERNS

- Never import atomic components directly — use `t.sci_pro_<name>()`.
- `category_panel.py` stores checkbox states at dynamic composite keys (`"{slug}::{sentiment}::{text}"`) — these are NOT in `DEFAULT_STATE`, violating rule #10.
- Fetching `self.application.state.get(key, False)` for each checkbox — consider batch reads.
