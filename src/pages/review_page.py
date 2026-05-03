"""Main grading interface: rubric checkboxes, scoring inputs, evaluation text.

This page implements the core review loop:
1. Selecting criteria sub-points (categorized by sentiment).
2. Scoring grading dimensions via sliders.
3. Generating and exporting evaluation text.
4. Managing session state with undo/redo.
5. Auto-saving to IndexedDB after each mutation.
"""

from __future__ import annotations

import asyncio
import logging

from puepy import t
from puepy.exceptions import Redirect
from puepy.runtime import window
from pyodide.ffi import create_proxy

from src.pages.base_page import BasePage
from src.services.grading_config import DEFAULT_GRADING_CONFIG
from src.services.text_generator import generate_evaluation_text
from src.state import ReviewState, session_to_dict

logger = logging.getLogger(__name__)

# Storage module is optional (not available under pytest).
try:
    from src.browser.storage import get_storage, make_review_record
except (ImportError, Exception):
    get_storage = None
    make_review_record = None


class ReviewPage(BasePage):
    """Core review workspace with layout matching SvelteKit parity."""

    redraw_on_app_state_changes = [
        "criteria_bundle",
        "assignment_id",
        "student_id",
        "mode",
        "active_tab",
        "is_mobile",
        "grading_inputs",
        "grade_result",
    ]

    def bind(self) -> None:
        """Initialize state and event listeners."""
        # Initial mobile check
        is_mobile = window.innerWidth < 1024
        self.application.state["is_mobile"] = is_mobile
        self.application.state.setdefault("active_tab", "criteria")

        # Resize listener
        self._resize_proxy = create_proxy(self._on_resize)
        window.addEventListener("resize", self._resize_proxy)

    def unbind(self) -> None:
        """Cleanup listeners."""
        if hasattr(self, "_resize_proxy"):
            window.removeEventListener("resize", self._resize_proxy)
            self._resize_proxy.destroy()

    def _on_resize(self, _event=None) -> None:
        is_mobile = window.innerWidth < 1024
        if is_mobile != self.application.state.get("is_mobile"):
            self.application.state["is_mobile"] = is_mobile

    def on_ready(self) -> None:
        """Load data if missing after mount."""
        super().on_ready()

        # Async criteria loading if missing
        bundle = self.application.state.get("criteria_bundle")
        assignment_id = self.application.state.get("assignment_id")

        if assignment_id and not bundle:

            async def _load():
                try:
                    from src.services.criteria_loader import load_criteria_bundle

                    loaded_bundle = load_criteria_bundle(assignment_id)
                    self.application.state["criteria_bundle"] = loaded_bundle
                except Exception as e:
                    logger.error("Failed to load criteria: %s", e)
                    raise Redirect("/") from None

            asyncio.ensure_future(_load())

        # Restore session from IndexedDB if available
        if get_storage:

            async def _restore():
                try:
                    storage = get_storage()
                    data = await storage.load_current_session()
                    if data:
                        from src.state import dict_to_session

                        session = dict_to_session(data)
                        rs = ReviewState(self.application.state)
                        rs.load_from_session(session)
                        self.application.state["notification"] = "Previous session restored."
                except Exception as e:
                    logger.debug("Storage load error: %s", e)

            asyncio.ensure_future(_restore())

    def populate_content(self) -> None:
        """Render the review interface with SvelteKit-parity layout."""
        bundle = self.application.state.get("criteria_bundle")
        assignment_id = self.application.state.get("assignment_id", "")
        student_id = self.application.state.get("student_id", "")
        mode = self.application.state.get("mode", "teacher")
        is_mobile = self.application.state.get("is_mobile", False)
        active_tab = self.application.state.get("active_tab", "criteria")

        if not assignment_id:
            raise Redirect("/")

        if not bundle:
            self._render_loading_skeleton()
            return

        # 1. Assignment Info Bar
        if student_id:
            with t.div(
                class_name="mb-6 flex items-center gap-3 bg-muted/30 px-4 py-2 rounded-lg border border-border/50"
            ):
                t.span(
                    "Student:", class_name="text-xs text-muted-foreground uppercase font-semibold"
                )
                t.span(student_id, class_name="text-sm font-medium font-mono")
                t.span("·", class_name="text-muted-foreground")
                t.span(
                    "Assignment:",
                    class_name="text-xs text-muted-foreground uppercase font-semibold",
                )
                t.span(bundle.assignment_name, class_name="text-sm font-medium")

        # 2. Main Workspace Layout
        if is_mobile and mode == "teacher":
            # Mobile Teacher: Tabs
            with t.sci_pro_tabs(value=active_tab, on_change=self._on_tab_change):
                with t.sci_pro_tabs_list():
                    t.sci_pro_tabs_trigger("Criteria", value="criteria")
                    t.sci_pro_tabs_trigger("Grading", value="grading")
                    t.sci_pro_tabs_trigger("Evaluation", value="evaluation")

                with t.sci_pro_tabs_content(value="criteria"):
                    t.sci_pro_criteria_list()
                with t.sci_pro_tabs_content(value="grading"):
                    t.sci_pro_grading_sidebar(on_grading_change=self._on_grading_change)
                with t.sci_pro_tabs_content(value="evaluation"):
                    t.sci_pro_evaluation_output(on_generate=self._on_generate_text)

        elif is_mobile and mode == "student":
            # Mobile Student: List only
            t.sci_pro_criteria_list()

        else:
            # Desktop: Side-by-side
            with t.div(class_name="flex flex-col lg:flex-row gap-8 items-start"):
                # Left Column: Criteria + Evaluation
                with t.div(class_name="flex-1 space-y-8 w-full"):
                    t.sci_pro_criteria_list()
                    if mode == "teacher":
                        t.sci_pro_evaluation_output(on_generate=self._on_generate_text)

                # Right Column: Grading (Sticky)
                if mode == "teacher":
                    with t.div(class_name="lg:sticky lg:top-8 w-full lg:w-auto"):
                        t.sci_pro_grading_sidebar(on_grading_change=self._on_grading_change)

        # 3. Sticky Footer
        t.sci_pro_review_footer(on_save=self._on_save)

    def _on_tab_change(self, event) -> None:
        self.application.state["active_tab"] = event.detail["value"]

    def _on_grading_change(self, event) -> None:
        dim = event.detail["dimension"]
        val = event.detail["value"]
        rs = ReviewState(self.application.state)
        rs.set_grading_input(dim, val)

        # Trigger recalculation immediately so the sidebar updates correctly
        from src.services.grade_calculator import calculate_grade

        try:
            res = calculate_grade(self.application.state["grading_inputs"], DEFAULT_GRADING_CONFIG)
            self.application.state["grade_result"] = res
        except Exception:
            pass

        asyncio.ensure_future(self._auto_save())

    def _on_generate_text(self, _e=None) -> None:
        """Call text generation service and update state."""
        criteria_bundle = self.application.state.get("criteria_bundle")
        if not criteria_bundle:
            self.application.state["notification"] = "Error: Criteria not loaded"
            return

        rs = ReviewState(self.application.state)
        text = generate_evaluation_text(rs.to_session(), criteria_bundle)
        self.application.state["generated_text"] = text
        self.application.state["notification"] = "Report generated"

    async def _on_save(self, _e=None) -> None:
        """Save the current session to persistent storage."""
        if not get_storage or not make_review_record:
            return
        try:
            from src.state import ReviewState, session_to_dict

            rs = ReviewState(self.application.state)
            session = rs.to_session()
            grade_result = self.application.state.get("grade_result")

            # Ensure grade result is in dict format
            if hasattr(grade_result, "model_dump"):
                grade_result_dict = grade_result.model_dump()
            else:
                grade_result_dict = grade_result or {}

            # Get serializable session data
            session_data = session_to_dict(session)

            record = make_review_record(
                student_id=session.student_id,
                assignment_id=session.assignment_id,
                category_selections=session_data["category_selections"],
                grading_inputs=session.grading_inputs,
                grade_result=grade_result_dict,
                generated_text=session.generated_text,
                existing_id=self.application.state.get("current_review_id", "") or "",
            )

            storage = get_storage()
            await storage.open_db()
            await storage.save_review(record)

            self.application.state["notification"] = "Review saved to database"
        except Exception as e:
            logger.error("Save error: %s", e)
            self.application.state["notification"] = f"Failed to save review: {e}"

    async def _auto_save(self) -> None:
        """Debounced auto-save to IndexedDB 'current_session'."""
        if not get_storage:
            return
        try:
            rs = ReviewState(self.application.state)
            await get_storage().save_current_session(session_to_dict(rs.to_session()))
        except Exception:
            pass

    def _render_loading_skeleton(self) -> None:
        """Render a placeholder while criteria bundle is loading."""
        with t.div(class_name="space-y-6"):
            with t.div(class_name="flex items-center justify-between flex-wrap gap-4"):
                t.sci_pro_skeleton(variant="text", class_name="h-8 w-64")
                t.sci_pro_skeleton(variant="text", class_name="h-10 w-48")

            with t.div(class_name="flex flex-col lg:flex-row gap-6"):
                # Main content skeleton
                with t.div(class_name="flex-1 space-y-4"):
                    for _ in range(3):
                        with t.sci_pro_card():
                            with t.sci_pro_card_header():
                                t.sci_pro_skeleton(variant="text", class_name="h-6 w-1/3")
                            with t.sci_pro_card_content(class_name="space-y-2"):
                                for _ in range(4):
                                    t.sci_pro_skeleton(variant="text", class_name="h-4 w-full")

                # Sidebar skeleton
                with t.aside(class_name="w-full lg:w-80 space-y-6"):
                    with t.sci_pro_card():
                        with t.sci_pro_card_header():
                            t.sci_pro_skeleton(variant="text", class_name="h-6 w-1/2")
                        with t.sci_pro_card_content(class_name="space-y-4"):
                            for _ in range(3):
                                t.sci_pro_skeleton(variant="text", class_name="h-4 w-full")
                    with t.sci_pro_card():
                        with t.sci_pro_card_header():
                            t.sci_pro_skeleton(variant="text", class_name="h-6 w-1/2")
                        with t.sci_pro_card_content():
                            t.sci_pro_skeleton(variant="rectangle", class_name="h-32 w-full")
