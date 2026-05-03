from __future__ import annotations

from puepy import Component, t

from src.browser.theme_controller import toggle_theme


@t.component()
class SciProHeader(Component):
    """Application header with navigation toggle and theme switcher.

    Displays the page title, mode toggle buttons, and a theme cycle button.
    Redraws automatically when ``mode`` or ``theme`` app state changes.
    """

    component_name = "sci-pro-header"
    props = ["title"]
    redraw_on_app_state_changes = ["mode", "theme"]

    def populate(self):
        with t.header(
            class_name="flex items-center justify-between px-4 py-2 bg-base-100 border-b border-base-300"
        ):
            with t.div(class_name="flex items-center gap-2 font-bold text-lg"):
                t.span(self.props.title)

            with t.div(class_name="flex items-center gap-4"):
                t.sci_pro_mode_toggle()
                t.button(
                    "🌙" if self.application.state.get("theme") == "light" else "☀️",
                    class_name="btn btn-ghost btn-sm",
                    on_click=self._toggle_theme,
                )

    def _toggle_theme(self, _event=None):
        """Cycle theme: light -> dark -> system -> light."""
        new_theme = toggle_theme()
        self.application.state["theme"] = new_theme
