"""SciProReviewFooter — Sticky bottom bar for progress and session actions."""

from __future__ import annotations

from puepy import Component, Prop, t

from src.state import ReviewState


@t.component()
class SciProReviewFooter(Component):
    """Sticky footer with progress bar, undo/redo, and action buttons."""

    component_name = "sci-pro-review-footer"
    redraw_on_app_state_changes = ["can_undo", "can_redo", "category_selections"]

    props = [
        Prop("on_save", "Save button click handler", object, None),
    ]

    def populate(self) -> None:
        rs = ReviewState(self.application.state)
        progress = rs.category_progress
        filled = progress["filled"]
        total = progress["total"]
        percentage = (filled / total * 100) if total > 0 else 0

        with t.div(
            class_name="fixed bottom-0 left-0 lg:left-64 right-0 z-30 bg-background/80 backdrop-blur-md border-t border-border px-4 py-3 flex items-center justify-between gap-4"
        ):
            # Left: History Actions
            with t.div(class_name="flex items-center gap-1"):
                t.sci_pro_button(
                    variant="ghost",
                    icon="undo-2",
                    disabled=not rs.can_undo,
                    on_click=lambda _: self._on_undo(rs),
                    class_name="size-9 p-0",
                )
                t.sci_pro_button(
                    variant="ghost",
                    icon="redo-2",
                    disabled=not rs.can_redo,
                    on_click=lambda _: self._on_redo(rs),
                    class_name="size-9 p-0",
                )
                t.sci_pro_separator(orientation="vertical", class_name="h-4 mx-1")
                t.sci_pro_button(
                    variant="ghost",
                    icon="trash-2",
                    on_click=lambda _: self._on_reset(rs),
                    class_name="size-9 p-0 text-destructive hover:bg-destructive/10",
                )

            # Center: Progress (Absolute center on desktop, flex-1 on mobile)
            with t.div(
                class_name="hidden md:flex flex-col gap-1 items-center justify-center absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-64"
            ):
                with t.div(
                    class_name="flex items-center justify-between w-full text-[10px] font-bold uppercase tracking-wider text-muted-foreground"
                ):
                    t("Completion")
                    t(f"{filled}/{total} Categories")
                t.sci_pro_progress_bar(value=percentage, class_name="h-1.5 w-full")

            # Right: Actions
            with t.div(class_name="flex items-center gap-2"):
                t.sci_pro_button(
                    variant="ghost",
                    label="Export",
                    icon="download",
                    on_click=self._on_export,
                    class_name="hidden sm:inline-flex",
                )

                on_save = self.props_values.get("on_save")
                t.sci_pro_button(
                    variant="primary",
                    label="Save Review",
                    icon="save",
                    on_click=on_save,
                    class_name="shadow-sm font-semibold",
                )

    def _on_undo(self, rs: ReviewState) -> None:
        rs.undo()
        self.page.redraw()

    def _on_redo(self, rs: ReviewState) -> None:
        rs.redo()
        self.page.redraw()

    def _on_reset(self, rs: ReviewState) -> None:
        if self.page.window.confirm("Are you sure you want to clear all selections?"):
            rs.reset_session()
            self.page.redraw()

    def _on_export(self, _e) -> None:
        from src.browser.files import download_json
        from src.state import session_to_dict

        rs = ReviewState(self.application.state)
        data = session_to_dict(rs.to_session())
        filename = f"review_{rs.student_id or 'export'}.json"

        download_json(data, filename)
        self.application.state["notification"] = f"Exported {filename}"
