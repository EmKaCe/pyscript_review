"""SciPro Review Application — PyScript/PuePy SPA root.

Creates the PuePy Application with Router, keyboard shortcuts,
initial state, and page route registrations.

The ``SciProReviewApp`` class uses the PuePy two-state model:
``self.state`` for ephemeral UI state, ``self.application.state`` for
all business data shared across pages.
"""

from __future__ import annotations

from collections.abc import Callable

from puepy import Application, Component, t  # type: ignore[import-untyped]
from puepy.router import Router  # type: ignore[import-untyped]
from puepy.runtime import window  # type: ignore[import-untyped]

# Import services and browser modules.
from src.browser.shortcuts import register_default_shortcuts
from src.browser.theme_controller import get_theme

# Import all atomic components to register with @t.component().
from src.components.atomic import (  # noqa: F401
    SciProBadge,
    SciProButton,
    SciProCard,
    SciProCardContent,
    SciProCardDescription,
    SciProCardFooter,
    SciProCardHeader,
    SciProCardTitle,
    SciProCheckbox,
    SciProIcon,
    SciProInput,
    SciProInputGroup,
    SciProProgressBar,
    SciProSelect,
    SciProSeparator,
    SciProSkeleton,
    SciProSlider,
    SciProTable,
    SciProTableBody,
    SciProTableCell,
    SciProTableHead,
    SciProTableHeader,
    SciProTableRow,
    SciProTextarea,
    SciProTooltip,
)

# Import feature composite components.
from src.components.feature.criteria_list import SciProCriteriaList
from src.components.feature import (  # noqa: F401
    SciProDropdownMenu,
    SciProEvaluationOutput,
    SciProGradingSidebar,
    SciProHeader,
    SciProModeToggle,
    SciProPopover,
    SciProReviewFooter,
    SciProSidebarSheet,
    SciProTabs,
    SciProTabsContent,
    SciProTabsList,
    SciProTabsTrigger,
    SciProToaster,
    show_toast,
)

# Import pages.
from src.pages.about_page import AboutPage
from src.pages.home_page import HomePage
from src.pages.review_page import ReviewPage
from src.pages.settings_page import SettingsPage
from src.state import DEFAULT_STATE

# ---------------------------------------------------------------------------
# Initial state builder
# ---------------------------------------------------------------------------


def _build_initial_state() -> dict:
    """Build the app-wide state dict from DEFAULT_STATE + live data.

    Attempts to load assignments, theme preference, and other
    runtime data. Falls back to DEFAULT_STATE with a ``boot_error``
    key on failure.

    Returns:
        State dict suitable for ``Application.initial()``.
    """
    state = dict(DEFAULT_STATE)
    state["boot_error"] = None

    try:
        from src.services.criteria_loader import (
            get_assignments_from_criteria,
        )

        try:
            assignments = get_assignments_from_criteria()
            state["assignments"] = [a.model_dump() for a in assignments]
        except (FileNotFoundError, OSError, ValueError, KeyError):
            state["assignments"] = []

        theme = get_theme()
        state["theme"] = theme if theme in ("light", "dark", "system") else "light"

        return state

    except ImportError:
        # Running under pytest without full browser stack.
        state["assignments"] = []
        state["theme"] = "light"
        return state

    except FileNotFoundError as exc:
        state["boot_error"] = f"Data file missing: {exc}"
        return state

    except (OSError, ValueError, KeyError) as exc:
        state["boot_error"] = f"Boot failed: {exc}"
        return state


# ---------------------------------------------------------------------------
# Application class
# ---------------------------------------------------------------------------


class SciProReviewApp(Application):
    """Root PuePy Application for the SciPro Review SPA.

    Overrides ``initial()`` to populate the app-wide ReactiveDict with
    live criteria, theme, and assignment data at startup.
    """

    def initial(self) -> dict:
        """Return the initial state dict for the application."""
        return _build_initial_state()


# ---------------------------------------------------------------------------
# App instance, router, shortcuts
# ---------------------------------------------------------------------------

app = SciProReviewApp()
app.install_router(Router, link_mode=Router.LINK_MODE_HASH)


def _setup_keyboard_shortcuts(app_instance: SciProReviewApp) -> None:
    """Register global keyboard shortcuts bound to app state.

    Args:
        app_instance: The active SciProReviewApp instance whose state
            is mutated by shortcuts.
    """

    def _save_session() -> None:
        """Handle Ctrl+S — save notification."""
        app_instance.state["notification"] = "Session saved (persistence stub)"

    def _undo() -> None:
        """Handle Ctrl+Z — undo last action."""
        from src.state import ReviewState

        review = ReviewState(app_instance.state)
        review.undo()
        app_instance.state["notification"] = "Undo"

    def _redo() -> None:
        """Handle Ctrl+Shift+Z / Ctrl+Y — redo last undone action."""
        from src.state import ReviewState

        review = ReviewState(app_instance.state)
        review.redo()
        app_instance.state["notification"] = "Redo"

    def _mode_toggle() -> None:
        """Handle Alt+Shift+G — toggle teacher/student mode."""
        from puepy.runtime import window
        
        # Restrict mode toggle to settings page only
        hash_val = getattr(window.location, "hash", "")
        if hash_val != "#/settings":
            app_instance.state["notification"] = "Mode toggle restricted to Settings page"
            return

        current = app_instance.state.get("mode", "teacher")
        next_mode = "student" if current == "teacher" else "teacher"
        app_instance.state["mode"] = next_mode
        app_instance.state["notification"] = f"Switched to {next_mode} mode"

    def _escape_dismiss() -> None:
        """Handle Escape — dismiss notification."""
        app_instance.state["notification"] = ""

    callback_map: dict[str, Callable[[], None]] = {
        "save_session": _save_session,
        "undo": _undo,
        "redo_shift_z": _redo,
        "redo_y": _redo,
        "mode_toggle": _mode_toggle,
        "escape": _escape_dismiss,
    }

    register_default_shortcuts(callback_map)


_setup_keyboard_shortcuts(app)


# ---------------------------------------------------------------------------
# Boot error banner component
# ---------------------------------------------------------------------------


class BootErrorBanner(Component):
    """Banner displayed when ``boot_error`` is set in app state.

    Renders a destructive-coloured notice with a Reload button.
    Only appears in a live browser context (not pytest/SSR).
    """

    def populate(self) -> None:
        """Render the banner if boot_error is truthy."""
        error = self.application.state.get("boot_error")
        if not error:
            return

        with t.div(
            class_name="bg-destructive text-destructive-foreground p-3 flex items-center justify-between rounded-lg"
        ):
            with t.div(class_name="flex items-center gap-2"):
                t.span(":", class_name="text-lg")
                t.span(error, class_name="font-bold text-sm")
            t.button(
                "Reload",
                onclick=lambda _event: window.location.reload(),
                class_name="bg-background text-destructive px-3 py-1.5 rounded-md text-sm font-semibold hover:bg-muted",
            )


# ---------------------------------------------------------------------------
# Page route registration
# ---------------------------------------------------------------------------

app.page("/")(HomePage)
app.page("/review")(ReviewPage)
app.page("/settings")(SettingsPage)
app.page("/about")(AboutPage)


# ---------------------------------------------------------------------------
# Mount guard (SSR-safe)
# ---------------------------------------------------------------------------

if window is not None:
    app.mount("#app")
