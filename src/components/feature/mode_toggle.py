from __future__ import annotations

from puepy import Component, t
from puepy.runtime import window


@t.component()
class SciProModeToggle(Component):
    """Navigation mode selector rendered as a segmented button group.

    Displays Home / Review / Settings tabs. The active mode is highlighted
    with ``btn-primary``; inactive tabs use ``btn-ghost``.
    """

    component_name = "sci-pro-mode-toggle"
    props = []
    redraw_on_app_state_changes = ["mode"]

    def populate(self):
        current_mode = self.application.state.get("mode", "home")

        modes = [
            ("home", "Home"),
            ("review", "Review"),
            ("settings", "Settings"),
            ("docs", "Docs"),
        ]

        with t.div(class_name="flex gap-2 bg-secondary p-1 rounded-lg"):
            for mode_id, label in modes:
                is_active = current_mode == mode_id
                btn_class = "btn-primary" if is_active else "btn-ghost"

                t.button(
                    label,
                    class_name=f"btn {btn_class} btn-sm",
                    on_click=lambda _e, m=mode_id: self._set_mode(m),
                )

    def _set_mode(self, mode: str) -> None:
        """Set the application mode, triggering a page switch."""
        self.application.state["mode"] = mode

        path = "/"
        if mode == "review":
            path = "/review"
        elif mode == "settings":
            path = "/settings"
        elif mode == "docs":
            if window:
                window.location.href = "/docs-static/index.html"
            return
        elif mode == "home":
            path = "/"

        if self.application.router:
            self.application.router.navigate(f"#{path}")
