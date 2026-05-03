"""Home page — entry point for starting new reviews, importing, and loading saved sessions.

Provides:
- Welcome header.
- Action cards for "New Review" and "Import Review".
- List of recently saved reviews for quick loading.
"""

from __future__ import annotations

import asyncio
import logging

from puepy import t

from src.pages.base_page import BasePage

try:
    from src.browser.storage import get_storage
except ImportError:
    get_storage = None  # type: ignore[assignment]


logger = logging.getLogger(__name__)


class HomePage(BasePage):
    """Landing page with review creation, import, and saved review history."""

    redraw_on_app_state_changes = [
        "assignments",
        "saved_reviews",
        "current_semester",
    ]

    def on_ready(self) -> None:
        """Load saved reviews from IndexedDB when the page becomes active."""
        try:
            from js import window  # type: ignore[import-untyped]

            if hasattr(window, "basecoat"):
                window.basecoat.initAll()
        except ImportError:
            pass

        if get_storage is None:
            return

        async def _load_reviews() -> None:
            try:
                storage = get_storage()
                await storage.open_db()
                reviews = await storage.list_reviews()
                self.application.state["saved_reviews"] = [
                    {
                        "id": r.id,
                        "student_id": r.student_id,
                        "assignment_id": r.assignment_id,
                        "semester": r.semester,
                        "grade": (r.grade_result.get("grade", "N/A") if r.grade_result else "N/A"),
                        "updated_at": r.updated_at,
                    }
                    for r in reviews
                ]
            except Exception as e:
                logger.debug("Failed to load from storage: %s", e)

        asyncio.ensure_future(_load_reviews())

    def populate_content(self) -> None:
        """Render home content."""
        with t.div(class_name="mb-8"):
            with t.h1(class_name="text-2xl font-bold tracking-tight"):
                t.span("SciPro Review")
            with t.p(class_name="text-sm text-muted-foreground mt-1"):
                t.span("Peer review and grading tool for scientific programming courses")

        with t.div(class_name="flex flex-col gap-6"):
            with t.div(class_name="grid grid-cols-1 md:grid-cols-2 gap-6"):
                t.sci_pro_new_review_card(ref="home-new-review-card")
                t.sci_pro_import_review_card(ref="home-import-review-card")

            t.sci_pro_load_review_card(ref="home-load-review-card")
