"""SciProImportReviewCard — Feature component for importing review data from JSON.

Provides a drag-and-drop zone and file picker to load a saved review session
from a JSON file. Matches the svelte import-review-card reference design with
icon badge header, dashed drop zone, and conditional status bar.
"""

import asyncio
import json
import logging

from puepy import Component, t

logger = logging.getLogger(__name__)


@t.component()
class SciProImportReviewCard(Component):
    """Card to import a review session from a JSON file via drag-and-drop or file picker.

    Registered as ``t.sci_pro_import_review_card()``.

    Uses ``self.state`` for UI-local flags (drag-over, status, status message)
    and ``self.application.state["import_state"]`` for app-wide import tracking.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-import-review-card"

    redraw_on_state_changes = ["is_drag_over", "status", "status_message"]

    def initial(self):
        return {
            "is_drag_over": False,
            "status": "idle",
            "status_message": "",
        }

    def populate(self) -> None:
        """Render the import review card matching the svelte reference design."""
        is_drag_over = self.state.get("is_drag_over", False)
        status = self.state.get("status", "idle")

        with t.sci_pro_card(class_name="hover:shadow-md transition-shadow"):
            with t.sci_pro_card_header(class_name="flex items-center gap-3"):
                with t.div(
                    class_name="h-10 w-10 rounded-lg bg-blue-500/10 text-blue-600 flex items-center justify-center"
                ):
                    t.sci_pro_icon(name="upload", size="md")

                with t.div():
                    with t.sci_pro_card_title(class_name="text-base"):
                        t.span("Import Review")
                    with t.sci_pro_card_description():
                        t.span("Load from a JSON file")

            with t.sci_pro_card_content():
                drop_classes = "flex flex-col items-center gap-3 border-2 border-dashed rounded-lg p-6 transition-colors cursor-pointer"
                if is_drag_over:
                    drop_classes += " border-primary bg-primary/5"

                with t.div(
                    class_name=drop_classes,
                    role="button",
                    tabindex="0",
                    on_click=self._on_drop_zone_click,
                    on_dragover=self._on_drag_over,
                    on_dragleave=self._on_drag_leave,
                    on_drop=self._on_drop,
                    on_keydown=self._on_drop_zone_keydown,
                ):
                    with t.div(class_name="h-8 w-8 text-muted-foreground"):
                        t.sci_pro_icon(name="upload", size="xl")

                    with t.div(class_name="text-center"):
                        with t.p(class_name="text-sm font-medium"):
                            t.span("Drag & drop a JSON file here")
                        with t.p(class_name="text-xs text-muted-foreground"):
                            t.span("or click to browse")

                if status != "idle":
                    msg = self.state.get("status_message", "")
                    is_success = status == "success"
                    text_class = (
                        "text-sm text-green-600" if is_success else "text-sm text-destructive"
                    )

                    with t.div(class_name="mt-3 flex items-center gap-2"):
                        with t.span(class_name=text_class):
                            t(msg)
                        t.sci_pro_button(
                            variant="ghost",
                            label="Dismiss",
                            on_click=self._on_dismiss,
                        )

    def _on_drop_zone_click(self, _event=None) -> None:
        """Open the native browser file picker when the drop zone is clicked."""
        self._trigger_file_picker()

    def _on_drop_zone_keydown(self, event=None) -> None:
        """Trigger file picker on Enter key for accessibility."""
        try:
            key = getattr(event, "key", "")
            if key == "Enter":
                self._trigger_file_picker()
        except Exception:  # noqa: BLE001
            pass

    def _on_drag_over(self, event=None) -> None:
        """Highlight the drop zone when a file is dragged over it."""
        self.state["is_drag_over"] = True
        if event is not None:
            try:  # noqa: SIM105
                event.preventDefault()
            except Exception:  # noqa: BLE001
                pass

    def _on_drag_leave(self, _event=None) -> None:
        """Remove the drop zone highlight when the drag leaves."""
        self.state["is_drag_over"] = False

    def _on_drop(self, event=None) -> None:
        """Handle a file dropped onto the drop zone."""
        self.state["is_drag_over"] = False
        if event is not None:
            try:
                event.preventDefault()
                dt = getattr(event, "dataTransfer", None)
                if dt is None:
                    return
                files = dt.files
                if files is None or files.length == 0:
                    return
                file_obj = files.item(0)
                if file_obj is not None:
                    self._read_file(file_obj)
            except Exception as e:  # noqa: BLE001
                logger.debug("Drop handler error: %s", e)

    def _on_dismiss(self, _event=None) -> None:
        """Clear the status message bar."""
        self.state["status"] = "idle"
        self.state["status_message"] = ""
        self.application.state["import_state"] = ""

    def _trigger_file_picker(self, _event=None) -> None:
        """Open the native browser file picker for .json files."""
        try:
            from js import document
            from pyodide.ffi import create_proxy
        except ImportError:
            return

        self.application.state["import_state"] = "importing"
        self.state["status"] = "idle"
        self.state["status_message"] = ""

        input_el = document.createElement("input")
        input_el.type = "file"
        input_el.accept = ".json"
        input_el.style.display = "none"

        proxy = create_proxy(self._on_file_selected)
        input_el.addEventListener("change", proxy)

        document.body.appendChild(input_el)
        input_el.click()
        document.body.removeChild(input_el)

    def _on_file_selected(self, event: object) -> None:
        """Handle the file selection event from the native file picker."""
        file_obj = event.target.files.item(0)
        if not file_obj:
            self.state["status"] = "idle"
            self.state["status_message"] = ""
            self.application.state["import_state"] = ""
            return
        self._read_file(file_obj)

    def _read_file(self, file_obj: object) -> None:
        """Read a file object using the FileReader API and import its contents."""
        try:
            from js import FileReader
            from pyodide.ffi import create_proxy
        except ImportError:
            self.state["status"] = "error"
            self.state["status_message"] = "FileReader not available"
            self.application.state["import_state"] = "error"
            return

        self.state["status"] = "idle"
        self.state["status_message"] = ""
        self.application.state["import_state"] = "importing"

        def _on_reader_load(_: object) -> None:
            try:
                raw = getattr(_reader, "result", None)
                parsed = json.loads(str(raw))
                asyncio.ensure_future(self._import_parsed(parsed))
            except Exception as e:
                logger.debug("JSON parse error: %s", e)
                self.state["status"] = "error"
                self.state["status_message"] = "Import failed. Please check the file."
                self.application.state["import_state"] = "error"

        _reader = FileReader.new()
        _reader.onload = create_proxy(_on_reader_load)
        _reader.readAsText(file_obj)

    async def _import_parsed(self, data: dict) -> None:
        """Import parsed JSON data into storage.

        Args:
            data: The deserialized JSON dict from the imported file.
        """
        try:
            from src.browser.storage import get_storage
            from src.models.db import DbExport, ReviewRecord

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
            count = result.get("imported", 0)
            skipped = result.get("skipped", 0)
            self.state["status"] = "success"
            self.state["status_message"] = f"Imported {count} reviews ({skipped} skipped)."
            self.application.state["import_state"] = "success"
        except Exception as e:
            logger.debug("Import failed: %s", e)
            self.state["status"] = "error"
            self.state["status_message"] = "Import failed. Please check the file."
            self.application.state["import_state"] = "error"
