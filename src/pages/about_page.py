"""About page — project info, keyboard shortcuts, and technology stack."""

from __future__ import annotations

import logging

from puepy import t

from src.browser.shortcuts import format_shortcut, get_shortcuts
from src.pages.base_page import BasePage

logger = logging.getLogger(__name__)

_APP_VERSION = "1.0.0"


class AboutPage(BasePage):
    """About page with app version, tech stack, and keyboard shortcut reference."""

    def initial(self) -> dict:
        """Local state for the About page."""
        return {"shortcuts": {}}

    def on_ready(self) -> None:
        """Load shortcuts data and re-init Basecoat JS after page transition."""
        super().on_ready()
        try:
            self.state["shortcuts"] = get_shortcuts()
        except Exception as e:
            logger.debug("Failed to load shortcuts: %s", e)
            self.state["shortcuts"] = {}

    def populate_content(self) -> None:
        """Render the About page content."""
        with t.div(class_name="space-y-8 max-w-4xl mx-auto py-4"):
            self._render_hero()
            self._render_about_card()
            self._render_shortcuts_card()
            self._render_tech_stack_card()
            self._render_footer()

    def _render_hero(self) -> None:
        """Page title and version badge."""
        with t.div(class_name="pt-4 pb-2"):
            with t.h1(class_name="text-4xl font-bold tracking-tight"):
                t.span("SciPro Review")
            with t.p(class_name="mt-2 text-lg text-muted-foreground"):
                t.span(f"Version {_APP_VERSION} — Academic Peer-Review System")

    def _render_about_card(self) -> None:
        """Project description card."""
        with t.sci_pro_card():
            with t.sci_pro_card_header(), t.sci_pro_card_title():
                t.span("About the Project")
            with t.sci_pro_card_content():
                with t.p(class_name="text-muted-foreground leading-relaxed"):
                    t.span(
                        "SciPro Review is an executable academic manuscript system "
                        "designed for university Python programming courses at the "
                        "Hochschule Bonn-Rhein-Sieg. It treats Jupyter notebooks as "
                        "formal academic submissions, providing a structured framework "
                        "for peer-review, grading, and evidence-based learning "
                        "verification."
                    )

    def _render_shortcuts_card(self) -> None:
        """Keyboard shortcuts reference table."""
        with t.sci_pro_card():
            with t.sci_pro_card_header(), t.sci_pro_card_title():
                t.span("Keyboard Shortcuts")
            with t.sci_pro_card_description():
                t.span("Quickly navigate and manage your review sessions using these keys.")
            with t.sci_pro_card_content():
                shortcuts = self.state.get("shortcuts", {})
                if not shortcuts:
                    with t.div(class_name="text-sm text-muted-foreground italic"):
                        t.span("No shortcuts available.")
                else:
                    with t.div(class_name="overflow-x-auto rounded-lg border"):
                        with t.table(
                            class_name="w-full text-sm text-left border-collapse",
                        ):
                            with t.thead(class_name="bg-muted text-muted-foreground"):
                                with t.tr():
                                    with t.th(class_name="px-4 py-2 font-medium"):
                                        t.span("Action")
                                    with t.th(class_name="px-4 py-2 font-medium"):
                                        t.span("Combination")

                            with t.tbody():
                                for _action, data in shortcuts.items():
                                    with t.tr(
                                        class_name="border-t border-border hover:bg-muted/50"
                                    ):
                                        with t.td(class_name="px-4 py-2"):
                                            t.span(data["description"])
                                        with t.td(class_name="px-4 py-2 font-mono"):
                                            t.span(
                                                format_shortcut(data["keys"]),
                                                class_name="text-xs",
                                            )

    def _render_tech_stack_card(self) -> None:
        """Technology stack details."""
        with t.sci_pro_card():
            with t.sci_pro_card_header(), t.sci_pro_card_title():
                t.span("Technology Stack")
            with t.sci_pro_card_content():
                with t.div(class_name="grid grid-cols-1 sm:grid-cols-2 gap-4"):
                    stack = [
                        ("Python", "3.13"),
                        ("PyScript", "2026.3.1"),
                        ("PuePy", "0.6.5"),
                        ("Basecoat CSS", "0.3.11"),
                        ("Tailwind CSS", "v4"),
                        ("IndexedDB", "Client-side Storage"),
                    ]
                    for tech, ver in stack:
                        with t.div(
                            class_name="flex justify-between p-3 rounded-md bg-muted/30 text-sm"
                        ):
                            t.span(tech, class_name="font-medium")
                            t.span(ver, class_name="text-muted-foreground")

    def _render_footer(self) -> None:
        """Footer with university attribution and GitHub link."""
        with t.div(class_name="text-center py-8 text-xs text-muted-foreground space-y-2"):
            with t.p():
                t.span("Built for Hochschule Bonn-Rhein-Sieg")
            with t.a(
                href="https://github.com/ohmyopen-code/scipro",
                class_name="underline underline-offset-2 hover:text-primary",
            ):
                t.span("View Source on GitHub")
