"""Settings page — application preferences, theme, and data management.

Provides:
- Theme selection (Light, Dark, System) via segmented buttons.
- Keyboard shortcuts reference.
- Export/Import/Clear data controls.
- System and version information.
"""

from __future__ import annotations

import asyncio
import json
import logging

from puepy import t

from src.browser.files import download_json
from src.browser.shortcuts import format_shortcut, get_shortcuts
from src.browser.storage import get_storage
from src.browser.theme_controller import set_theme
from src.pages.base_page import BasePage

try:
    from js import window  # type: ignore[import-untyped]
except ImportError:
    window = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

_APP_VERSION = "1.0.0-alpha"


class SettingsPage(BasePage):
    """Application settings: theme, data import/export, keyboard shortcuts reference."""

    redraw_on_app_state_changes = ["mode", "theme", "current_semester", "notification"]

    def populate_content(self) -> None:
        """Render settings content: theme, shortcuts, data, and about."""
        semester = self.application.state.get("current_semester", "Unknown")

        with t.div(class_name="mb-8 flex items-center gap-3"):
            with t.div(
                class_name="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary"
            ):
                t.sci_pro_icon(name="settings", size="md")
            with t.div():
                t.h1("Settings", class_name="text-2xl font-bold tracking-tight")
                t.p(
                    "Configure review preferences and keyboard shortcuts",
                    class_name="text-sm text-muted-foreground",
                )

        with t.div(class_name="flex flex-col gap-8 max-w-2xl"):
            self._render_appearance_section()
            t.sci_pro_separator()
            self._render_review_mode_section()
            t.sci_pro_separator()
            self._render_shortcuts_section()
            t.sci_pro_separator()
            self._render_data_section()
            t.sci_pro_separator()
            self._render_semester_section(semester)

    def _render_appearance_section(self) -> None:
        """Theme mode selector with visual cards."""
        current_theme = self.application.state.get("theme", "light")
        
        with t.section():
            with t.div(class_name="flex items-center gap-2 mb-4"):
                t.sci_pro_icon(name="palette", size="sm", class_name="text-muted-foreground")
                t.h2("Appearance", class_name="text-lg font-semibold")
            
            with t.div(class_name="grid grid-cols-1 sm:grid-cols-3 gap-4"):
                # Light Theme Card
                self._render_theme_card("light", "sun", "Light", current_theme == "light")
                # Dark Theme Card
                self._render_theme_card("dark", "moon", "Dark", current_theme == "dark")
                # System Theme Card
                self._render_theme_card("system", "laptop", "System", current_theme == "system")

    def _render_theme_card(self, theme_id: str, icon: str, label: str, is_active: bool) -> None:
        """Render a clickable card for a specific theme."""
        active_cls = " ring-2 ring-primary border-primary bg-primary/5" if is_active else " hover:border-primary/50"
        
        with t.div(
            class_name=f"relative cursor-pointer transition-all duration-200 flex flex-col items-center justify-center p-6 border rounded-xl gap-3 {active_cls}",
            on_click=lambda _e, t=theme_id: self._on_theme_change(t)
        ):
            with t.div(class_name=f"p-3 rounded-full { 'bg-primary text-primary-foreground' if is_active else 'bg-muted text-muted-foreground' }"):
                t.sci_pro_icon(name=icon, size="md")
            t.span(label, class_name=f"font-semibold text-sm { 'text-primary' if is_active else 'text-muted-foreground' }")
            if is_active:
                with t.div(class_name="absolute top-2 right-2"):
                    t.sci_pro_badge(variant="default", label="Active", class_name="scale-75 origin-top-right")

    def _render_review_mode_section(self) -> None:
        """Review Mode selector."""
        with t.section():
            with t.div(class_name="flex items-center gap-2 mb-4"):
                t.sci_pro_icon(name="graduation-cap", size="sm", class_name="text-muted-foreground")
                t.h2("Review Mode", class_name="text-lg font-semibold")
            with t.sci_pro_card():
                with t.sci_pro_card_header():
                    t.sci_pro_card_title("Review Mode", class_name="text-base")
                    t.sci_pro_card_description("Switch between teacher and student view")
                with t.sci_pro_card_content(class_name="flex items-center justify-between"):
                    with t.div(class_name="flex items-center gap-3"):
                        mode = self.application.state.get("mode", "teacher")
                        label = mode.capitalize() if mode else "Unknown"
                        
                        if mode == "teacher":
                            badge_variant = "default"
                            desc = "Full grading with rubric and scores"
                        else:
                            badge_variant = "secondary"
                            desc = "Peer feedback only, no grading"

                        t.sci_pro_badge(variant=badge_variant, label=label)
                        t.span(desc, class_name="text-sm text-muted-foreground")

    def _render_shortcuts_section(self) -> None:
        """Keyboard shortcuts reference table."""
        with t.section():
            with t.div(class_name="flex items-center gap-2 mb-4"):
                t.sci_pro_icon(name="keyboard", size="sm", class_name="text-muted-foreground")
                t.h2("Keyboard Shortcuts", class_name="text-lg font-semibold")
            with t.sci_pro_card():
                with t.sci_pro_card_content(class_name="pt-6"):
                    shortcuts = get_shortcuts()
                    with t.div(class_name="flex flex-col divide-y"):
                        for _action, data in shortcuts.items():
                            with t.div(
                                class_name="flex items-center justify-between py-2.5 first:pt-0 last:pb-0"
                            ):
                                t.span(data["description"], class_name="text-sm")
                                with t.kbd(
                                    class_name="inline-flex items-center rounded border border-border bg-muted px-2 py-1 text-xs font-mono text-muted-foreground"
                                ):
                                    t(format_shortcut(data["keys"]))

    def _render_data_section(self) -> None:
        """Export/Import/Clear controls and Download Current Review."""
        with t.section():
            with t.div(class_name="flex items-center gap-2 mb-4"):
                t.sci_pro_icon(name="database", size="sm", class_name="text-muted-foreground")
                t.h2("Data", class_name="text-lg font-semibold")
            with t.div(class_name="flex flex-col gap-4"):
                with t.sci_pro_card():
                    with t.sci_pro_card_header():
                        t.sci_pro_card_title("Backup", class_name="text-base")
                        t.sci_pro_card_description(
                            "Export or import all saved reviews as a JSON file"
                        )
                    with t.sci_pro_card_content(class_name="flex items-center gap-3"):
                        t.sci_pro_button(
                            variant="outline", label="Export All", on_click=self._on_export_data
                        )
                        t.sci_pro_button(
                            variant="outline", label="Import Backup", on_click=self._on_import_data
                        )
                        t.sci_pro_button(
                            variant="outline",
                            label="Download Current Review",
                            on_click=self._on_download_current,
                        )
                with t.sci_pro_card():
                    with t.sci_pro_card_header():
                        t.sci_pro_card_title("Stored Reviews", class_name="text-base")
                        t.sci_pro_card_description("All reviews are saved locally in your browser")
                    with t.sci_pro_card_content(class_name="flex items-center justify-between"):
                        saved = self.application.state.get("saved_reviews", [])
                        count = len(saved)
                        t.span(
                            f"{count} review{'s' if count != 1 else ''} saved",
                            class_name="text-sm text-muted-foreground",
                        )
                        t.sci_pro_button(
                            variant="outline",
                            label="Delete All",
                            on_click=self._on_clear_data,
                            class_name="text-destructive hover:text-destructive",
                            disabled=count == 0,
                        )

    def _render_semester_section(self, semester: str) -> None:
        """Semester Information."""
        with t.section():
            with t.div(class_name="flex items-center gap-2 mb-4"):
                t.sci_pro_icon(name="calendar", size="sm", class_name="text-muted-foreground")
                t.h2("Semester", class_name="text-lg font-semibold")
            with t.sci_pro_card(class_name="overflow-hidden border-primary/20"):
                with t.div(class_name="bg-primary/5 px-6 py-8 flex flex-col items-center justify-center text-center"):
                    t.span("Current Academic Period", class_name="text-xs uppercase tracking-widest text-muted-foreground font-bold mb-2")
                    t.span(semester, class_name="text-4xl font-black tracking-tighter text-primary font-mono")
                    with t.p(class_name="mt-4 text-xs text-muted-foreground max-w-[240px]"):
                        t("This period is automatically determined based on the current date and system configuration.")

    # Event Handlers...
    def _on_theme_change(self, mode: str) -> None:
        """Apply selected theme mode."""
        set_theme(mode)
        self.application.state["theme"] = mode
        self.application.state["notification"] = f"Theme set to {mode}."

    async def _on_export_data(self) -> None:
        """Export all reviews from storage to JSON."""
        try:
            storage = get_storage()
            await storage.open_db()
            export = await storage.export_all()
            data = {
                "version": export.version,
                "exported_at": export.exported_at,
                "reviews": [
                    {
                        "id": r.id,
                        "student_id": r.student_id,
                        "assignment_id": r.assignment_id,
                        "semester": r.semester,
                        "category_selections": r.category_selections,
                        "grading_inputs": r.grading_inputs,
                        "grade_result": r.grade_result,
                        "generated_text": r.generated_text,
                        "created_at": r.created_at,
                        "updated_at": r.updated_at,
                    }
                    for r in export.reviews
                ],
            }
            download_json(data, "reviews_export.json")
            self.application.state["notification"] = f"Exported {len(export.reviews)} reviews."
        except Exception as e:
            logger.debug("Export failed: %s", e)
            self.application.state["notification"] = "Export failed."

    def _on_import_data(self) -> None:
        """Open file picker and import reviews from JSON."""
        if window is None:
            self.application.state["notification"] = "Import not available."
            return

        def _on_file_selected(event: object) -> None:
            file_obj = event.target.files.item(0)
            if not file_obj:
                return

            def _on_reader_load(_: object) -> None:
                try:
                    raw = getattr(_reader, "result", None)
                    parsed = json.loads(str(raw))
                    asyncio.ensure_future(self._import_parsed(parsed))
                except Exception as e:
                    logger.debug("JSON parse error: %s", e)
                    self.application.state["notification"] = "Invalid JSON file."

            _reader = __import__("js").FileReader.new()  # type: ignore[attr-defined]
            _reader.onload = __import__("pyodide.ffi").ffi.create_proxy(  # type: ignore[attr-defined]
                _on_reader_load
            )
            _reader.readAsText(file_obj)

        input_el = window.document.createElement("input")
        input_el.type = "file"
        input_el.accept = ".json"
        input_el.style.display = "none"
        from pyodide.ffi import create_proxy

        proxy = create_proxy(_on_file_selected)
        input_el.addEventListener("change", proxy)
        window.document.body.appendChild(input_el)
        input_el.click()
        window.document.body.removeChild(input_el)
        self.application.state["notification"] = "Import dialog opened."

    async def _import_parsed(self, data: dict) -> None:
        """Import parsed JSON data into storage."""
        from src.browser.storage import DbExport, ReviewRecord

        try:
            reviews = []
            for r in data.get("reviews", []):
                reviews.append(
                    ReviewRecord(
                        id=r.get("id", ""),
                        student_id=r.get("student_id", ""),
                        assignment_id=r.get("assignment_id", ""),
                        semester=r.get("semester", ""),
                        category_selections=r.get("category_selections", {}),
                        grading_inputs=r.get("grading_inputs", {}),
                        grade_result=r.get("grade_result", {}),
                        generated_text=r.get("generated_text", ""),
                        created_at=r.get("created_at", ""),
                        updated_at=r.get("updated_at", ""),
                    )
                )
            export = DbExport(
                version=data.get("version", 1),
                exported_at=data.get("exported_at", ""),
                reviews=reviews,
            )
            storage = get_storage()
            await storage.open_db()
            result = await storage.import_all(export)
            self.application.state["notification"] = (
                f"Imported {result['imported']} reviews ({result['skipped']} skipped)."
            )
        except Exception as e:
            logger.debug("Import failed: %s", e)
            self.application.state["notification"] = "Import failed."

    async def _on_download_current(self) -> None:
        """Export current review session as JSON."""
        from src.state import ReviewState, session_to_dict

        rs = ReviewState(self.application.state)
        session = rs.to_session()
        data = session_to_dict(session)
        download_json(data, "current_review.json")
        self.application.state["notification"] = "Current review downloaded."

    async def _on_clear_data(self) -> None:
        """Wipe all stored reviews after user confirmation."""
        if window is not None:
            confirmed = window.confirm(
                "Are you sure you want to delete all stored reviews? This cannot be undone."
            )
            if not confirmed:
                return

        try:
            storage = get_storage()
            await storage.open_db()
            await storage.clear_all_reviews()
            self.application.state["saved_reviews"] = []
            self.application.state["notification"] = "All data cleared successfully."
        except Exception as e:
            logger.debug("Clear data failed: %s", e)
            self.application.state["notification"] = "Clear failed."
