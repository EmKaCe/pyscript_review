"""SciProCategoryPanel — A feature component for rendering a rubric category.

Renders three sentiment sections (positive, neutral, negative) containing
checkbox-based rubric points, and an optional notes textarea.
"""

from __future__ import annotations

from puepy import Component, Prop, t

from src.models.criteria import Category
from src.state import ReviewState


@t.component()
class SciProCategoryPanel(Component):
    """Panel for a single rubric category with sentiment-grouped points."""

    component_name = "sci-pro-category-panel"

    props = [
        Prop("category", "The Category model to render", Category, None),
        Prop("category_key", "State key for the category", str, ""),
        Prop("selections", "Current selections for this category", None, None),
    ]

    def populate(self) -> None:
        """Render the category panel layout."""
        category: Category | None = self.props_values.get("category")
        if not category:
            return

        rs = ReviewState(self.application.state)
        category_slug = category.slug
        selections = rs.category_selections.get(category_slug)
        checked_items = selections.checked_items if selections else []
        notes = selections.notes if selections else ""

        # Sentiment group configurations
        sentiment_groups = [
            ("positive", "Positive Aspects", "i-lucide-check-circle", "text-green-600", "bg-green-50/50 border-green-100"),
            ("neutral", "Observations", "i-lucide-info", "text-blue-600", "bg-blue-50/50 border-blue-100"),
            ("negative", "Areas for Improvement", "i-lucide-alert-circle", "text-red-600", "bg-red-50/50 border-red-100"),
        ]

        with t.div(class_name="space-y-4"):
            for sentiment, label, icon, icon_color, section_style in sentiment_groups:
                points = [mp for mp in category.main_points if mp.sentiment.value == sentiment]
                if not points:
                    continue

                with t.div(class_name=f"rounded-lg border p-3 {section_style}"):
                    with t.div(class_name="flex items-center gap-2 mb-3"):
                        t.i(class_name=f"{icon} {icon_color} size-4")
                        t.span(label, class_name="text-xs font-bold uppercase tracking-wider opacity-70")

                    with t.div(class_name="space-y-4"):
                        for mp in points:
                            with t.div(class_name="space-y-2"):
                                t.p(mp.text, class_name="text-sm font-semibold")
                                with t.div(class_name="grid grid-cols-1 gap-1.5"):
                                    for sp in mp.sub_points:
                                        point_id = sp.id or sp.text
                                        is_checked = point_id in checked_items

                                        with t.label(class_name="flex items-start gap-2 bg-background/30 p-1.5 rounded hover:bg-background/50 cursor-pointer transition-colors"):
                                            t.sci_pro_checkbox(
                                                checked=is_checked,
                                                on_change=lambda _e, pid=point_id: self._on_toggle(category_slug, pid)
                                            )
                                            t.span(sp.text, class_name="text-sm leading-snug")

            # Comment Box
            with t.div(class_name="mt-4 pt-4 border-t"):
                t.sci_pro_textarea(
                    label="Notes",
                    placeholder="Specific observations...",
                    value=notes,
                    on_blur=lambda e: self._on_comment(category_slug, e.target.value),
                    class_name="text-xs"
                )

    def _on_toggle(self, category_slug: str, point_id: str) -> None:
        rs = ReviewState(self.application.state)
        rs.toggle_checkbox(category_slug, point_id)
        self.trigger_event("change")

    def _on_comment(self, category_slug: str, text: str) -> None:
        rs = ReviewState(self.application.state)
        rs.set_comment(category_slug, text)
        self.trigger_event("change")
