"""SciProLoadReviewCard — Feature card showing saved reviews as a sortable, filterable table.

Renders a Basecoat-styled card with a table listing saved reviews from
``application.state["saved_reviews"]``. Supports column-sort toggling,
text filtering by student ID or assignment name, and semester/assignment
dropdown filters. Matches the svelte load-review-card design.
"""

import contextlib

from puepy import Component, t

_MONTHS = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@t.component()
class SciProLoadReviewCard(Component):
    """Card with a table of saved reviews, sortable by column and filterable.

    State model (all UI-local via ``self.state``):
        sort_column: Column key currently sorted (``"student"`` | ``"assignment"``
            | ``"grade"`` | ``"updated"``). ``""`` means no sort active.
        sort_desc: ``True`` for descending, ``False`` for ascending.
        filter_text: Case-insensitive substring filter on student / assignment.
        filter_semester: Selected semester filter (``""`` = all).
        filter_assignment: Selected assignment filter (``""`` = all).

    Business data is read from ``self.application.state["saved_reviews"]``,
    a list of dicts with keys ``student_id``, ``assignment_id``, ``grade``,
    ``updated_at``, ``semester``, ``review_id``.
    """

    component_name = "sci-pro-load-review-card"

    redraw_on_app_state_changes = ["saved_reviews"]

    COLUMNS: list[tuple[str, str]] = [
        ("student", "Student"),
        ("assignment", "Assignment"),
        ("grade", "Grade"),
        ("updated", "Updated"),
        ("actions", "Actions"),
    ]

    def default_initial_state(self) -> dict:
        """Return initial UI-local state for sort, filter, and dropdowns."""
        return {
            "sort_column": "updated",
            "sort_desc": True,
            "filter_text": "",
            "filter_semester": "",
            "filter_assignment": "",
        }

    @staticmethod
    def _format_date(iso_str: str) -> str:
        """Format an ISO date string as ``Mon DD, HH:MM``.

        Args:
            iso_str: ISO 8601 date string (e.g. ``2025-04-30T14:05:00``).

        Returns:
            Human-readable date string or the original string on parse failure.
        """
        if not iso_str:
            return ""
        try:
            date_part = iso_str[:10]
            parts = date_part.split("-")
            int(parts[0])
            month = int(parts[1])
            day = int(parts[2])
            time_part = ""
            if "T" in iso_str:
                time_part = iso_str[iso_str.index("T") + 1 : iso_str.index("T") + 6]
            month_name = _MONTHS[month - 1] if 1 <= month <= 12 else str(month)
            result = (
                f"{month_name} {day:02d}, {time_part}" if time_part else f"{month_name} {day:02d}"
            )
            return result
        except (ValueError, IndexError):
            return iso_str

    def _get_assignment_name(self, assignment_id: str) -> str:
        """Resolve an assignment ID to its display name.

        Args:
            assignment_id: The assignment ID to look up.

        Returns:
            The assignment name from app state, or the raw ID if not found.
        """
        assignments: list[dict] = self.application.state.get("assignments", [])
        for a in assignments:
            if a.get("id") == assignment_id:
                return a.get("name", assignment_id)
        return assignment_id

    def _get_unique_semesters(self, reviews: list[dict]) -> list[str]:
        """Extract sorted unique semesters from reviews.

        Args:
            reviews: List of review dicts.

        Returns:
            Sorted list of unique semester strings.
        """
        semesters: set[str] = set()
        for r in reviews:
            sem = r.get("semester", "")
            if sem:
                semesters.add(sem)
        return sorted(semesters)

    def _get_unique_assignments(self, reviews: list[dict]) -> list[str]:
        """Extract sorted unique assignment IDs from reviews.

        Args:
            reviews: List of review dicts.

        Returns:
            Sorted list of unique assignment ID strings.
        """
        assignments: set[str] = set()
        for r in reviews:
            aid = r.get("assignment_id", "")
            if aid:
                assignments.add(aid)
        return sorted(assignments)

    def _apply_filter(self, reviews: list[dict], filter_text: str) -> list[dict]:
        """Filter reviews by case-insensitive substring match.

        Matches against student_id, assignment name, semester, and grade.

        Args:
            reviews: List of review dicts.
            filter_text: Substring to search for.

        Returns:
            Filtered list of review dicts.
        """
        if not filter_text:
            return list(reviews)
        lower: str = filter_text.lower()
        result: list[dict] = []
        for r in reviews:
            sid: str = r.get("student_id", "").lower()
            aid: str = r.get("assignment_id", "").lower()
            assign_name: str = self._get_assignment_name(r.get("assignment_id", "")).lower()
            grade: str = str(r.get("grade", "")).lower()
            semester: str = r.get("semester", "").lower()
            if (
                lower in sid
                or lower in aid
                or lower in assign_name
                or lower in grade
                or lower in semester
            ):
                result.append(r)
        return result

    def _apply_dropdown_filters(self, reviews: list[dict]) -> list[dict]:
        """Filter reviews by selected semester and assignment dropdowns.

        Args:
            reviews: List of review dicts.

        Returns:
            Filtered list matching both dropdown selections.
        """
        semester: str = self.state.get("filter_semester", "")
        assignment: str = self.state.get("filter_assignment", "")
        result: list[dict] = list(reviews)
        if semester:
            result = [r for r in result if r.get("semester", "") == semester]
        if assignment:
            result = [r for r in result if r.get("assignment_id", "") == assignment]
        return result

    def _apply_sort(self, reviews: list[dict]) -> list[dict]:
        """Sort reviews by the current sort column and direction.

        Args:
            reviews: List of review dicts.

        Returns:
            Sorted list of review dicts. Returns unsorted if no sort is active.
        """
        sort_col: str = self.state.get("sort_column", "")
        if not sort_col:
            return list(reviews)

        sort_desc: bool = self.state.get("sort_desc", True)
        reverse: bool = sort_desc

        key_map: dict[str, str] = {
            "student": "student_id",
            "assignment": "assignment_id",
            "grade": "grade",
            "updated": "updated_at",
        }
        review_key: str = key_map.get(sort_col, sort_col)

        def _sort_key(item: dict) -> str | float:
            val: object = item.get(review_key, "")
            if sort_col == "grade":
                try:
                    return float(val)  # type: ignore[arg-type]
                except (ValueError, TypeError):
                    return 0.0
            return str(val)

        return sorted(reviews, key=_sort_key, reverse=reverse)

    def _on_sort_click(self, col_key: str) -> None:
        """Toggle sort: ascending → descending → clear.

        Args:
            col_key: The column key being sorted.
        """
        current_col: str = self.state.get("sort_column", "")
        current_desc: bool = self.state.get("sort_desc", True)

        if current_col != col_key:
            self.state["sort_column"] = col_key
            self.state["sort_desc"] = False
        elif not current_desc:
            self.state["sort_desc"] = True
        else:
            self.state["sort_column"] = ""
            self.state["sort_desc"] = True

    def _on_filter_input(self, event: object) -> None:
        """Update filter_text state on input change.

        Args:
            event: DOM input event.
        """
        self.state["filter_text"] = event.target.value  # type: ignore[union-attr]

    def _on_semester_change(self, event: object) -> None:
        """Update semester filter on select change."""
        self.state["filter_semester"] = event.target.value  # type: ignore[union-attr]

    def _on_assignment_change(self, event: object) -> None:
        """Update assignment filter on select change."""
        self.state["filter_assignment"] = event.target.value  # type: ignore[union-attr]

    def _on_load(self, review: dict) -> None:
        """Load a saved review into application state and navigate to /review.

        Args:
            review: The review dict to load.
        """
        app_state = self.application.state
        app_state["student_id"] = review.get("student_id", "")
        app_state["assignment_id"] = review.get("assignment_id", "")
        app_state["current_review_id"] = review.get("review_id")
        with contextlib.suppress(AttributeError):
            self.application.router.navigate_to_path("/review")

    def _on_delete(self, review: dict) -> None:
        """Remove a review from saved_reviews and notify the user.

        Args:
            review: The review dict to delete.
        """
        review_id: str = review.get("review_id", "")
        reviews: list[dict] = list(self.application.state.get("saved_reviews", []))
        updated: list[dict] = [r for r in reviews if r.get("review_id") != review_id]
        self.application.state["saved_reviews"] = updated
        self.application.state["notification"] = "Review deleted"

    def populate(self) -> None:
        """Render the load-review card matching the svelte reference design."""
        all_reviews: list[dict] = self.application.state.get("saved_reviews", [])
        filter_text: str = self.state.get("filter_text", "")
        filtered: list[dict] = self._apply_filter(all_reviews, filter_text)
        filtered = self._apply_dropdown_filters(filtered)
        sorted_reviews: list[dict] = self._apply_sort(filtered)

        with t.sci_pro_card(class_name="hover:shadow-md transition-shadow"):
            with t.sci_pro_card_header(has_border=True):
                with t.div(class_name="flex items-center gap-3"):
                    with t.div(
                        class_name="h-10 w-10 rounded-lg bg-green-500/10 text-green-600 flex items-center justify-center"
                    ):
                        t.sci_pro_icon(name="file-text", size="md")
                    with t.div():
                        with t.sci_pro_card_title(class_name="text-base"):
                            t("Load Review")
                        with t.sci_pro_card_description():
                            t("Resume a saved review")

            with t.sci_pro_card_content():
                if not all_reviews:
                    with t.div(class_name="flex flex-col items-center gap-2 py-6 text-center"):
                        t.sci_pro_icon(
                            name="file-text",
                            size="xl",
                            class_name="text-muted-foreground/40",
                        )
                        with t.p(class_name="text-sm text-muted-foreground"):
                            t("No saved reviews yet")
                        with t.p(class_name="text-xs text-muted-foreground"):
                            t("Start or import a review to see it here")
                else:
                    self._render_filters(all_reviews)
                    self._render_search_row(len(sorted_reviews), len(all_reviews))
                    self._render_table(sorted_reviews)

    def _render_filters(self, all_reviews: list[dict]) -> None:
        """Render semester and assignment dropdown filters if needed.

        Only shown when there are multiple semesters or multiple assignments.

        Args:
            all_reviews: The unfiltered full list of reviews.
        """
        semesters: list[str] = self._get_unique_semesters(all_reviews)
        assignments: list[str] = self._get_unique_assignments(all_reviews)
        show_semester: bool = len(semesters) > 1
        show_assignment: bool = len(assignments) > 1

        if not show_semester and not show_assignment:
            return

        with t.div(class_name="flex flex-wrap items-center gap-3 mb-4"):
            if show_semester:
                semester_options: list[tuple[str, str]] = [("", "All Semesters")] + [
                    (s, s) for s in semesters
                ]
                with t.div(class_name="flex items-center gap-1.5"):
                    with t.span(class_name="text-xs text-muted-foreground font-medium"):
                        t("Semester")
                    t.sci_pro_select(
                        placeholder="All Semesters",
                        options=semester_options,
                        on_change=self._on_semester_change,
                    )

            if show_assignment:
                assignment_options: list[tuple[str, str]] = [("", "All Assignments")] + [
                    (a, self._get_assignment_name(a)) for a in assignments
                ]
                with t.div(class_name="flex items-center gap-1.5"):
                    with t.span(class_name="text-xs text-muted-foreground font-medium"):
                        t("Assignment")
                    t.sci_pro_select(
                        placeholder="All Assignments",
                        options=assignment_options,
                        on_change=self._on_assignment_change,
                    )

    def _render_search_row(self, match_count: int, total: int) -> None:
        """Render the search bar with result count.

        Args:
            match_count: Number of reviews matching current filters.
            total: Total number of reviews before filtering.
        """
        with t.div(class_name="flex items-center mb-3"):
            with t.div(class_name="flex-1"):
                with t.span(class_name="text-sm text-muted-foreground"):
                    t(f"{match_count} of {total} reviews")
            with t.div(class_name="w-64"):
                t.sci_pro_input(
                    placeholder="Search\u2026",
                    icon_prefix="search",
                    on_input=self._on_filter_input,
                    class_name="h-8 text-sm",
                )

    def _render_table(self, reviews: list[dict]) -> None:
        """Render the reviews table with sortable headers and action buttons.

        Args:
            reviews: Sorted and filtered list of review dicts to display.
        """
        with t.div(class_name="rounded-md border overflow-x-auto"):
            with t.sci_pro_table():
                with t.sci_pro_table_header():
                    with t.sci_pro_table_row():
                        for col_key, col_label in self.COLUMNS:
                            if col_key == "actions":
                                with t.sci_pro_table_head():
                                    t.span("Actions")
                            else:
                                self._render_sortable_header(col_key, col_label)

                with t.sci_pro_table_body():
                    if not reviews:
                        with t.sci_pro_table_row():
                            with t.sci_pro_table_cell(class_name="h-24 text-center", colspan="5"):
                                with t.div(class_name="flex flex-col items-center gap-1 py-4"):
                                    with t.p(class_name="text-sm text-muted-foreground"):
                                        t("No reviews match your search")
                                    with t.p(class_name="text-xs text-muted-foreground"):
                                        t("Try adjusting your filters")
                    else:
                        for review in reviews:
                            self._render_review_row(review)

    def _render_review_row(self, review: dict) -> None:
        """Render a single review table row.

        Args:
            review: A review dict with student_id, assignment_id, grade, updated_at.
        """
        row_class: str = "even:bg-muted/50"
        with t.sci_pro_table_row(class_name=row_class):
            with t.sci_pro_table_cell():
                t.span(review.get("student_id", ""))
            with t.sci_pro_table_cell():
                t.span(self._get_assignment_name(review.get("assignment_id", "")))
            with t.sci_pro_table_cell():
                grade_val: str = str(review.get("grade", ""))
                t.span(grade_val)
            with t.sci_pro_table_cell():
                t.span(self._format_date(review.get("updated_at", review.get("date", ""))))
            with t.sci_pro_table_cell():
                with t.div(class_name="flex gap-1"):
                    t.sci_pro_button(
                        variant="ghost",
                        label="Open",
                        on_click=lambda _e, r=review: self._on_load(r),
                    )
                    t.sci_pro_button(
                        variant="ghost",
                        label="Delete",
                        class_name="text-destructive hover:text-destructive",
                        on_click=lambda _e, r=review: self._on_delete(r),
                    )

    def _render_sortable_header(self, col_key: str, col_label: str) -> None:
        """Render a column header with sort indicator and click handler.

        Args:
            col_key: The data field key for sorting.
            col_label: The display label for the column.
        """
        sort_col: str = self.state.get("sort_column", "")
        sort_desc: bool = self.state.get("sort_desc", True)
        is_active: bool = sort_col == col_key

        indicator: str = ""
        if is_active and sort_desc:
            indicator = " ▼"
        elif is_active and not sort_desc:
            indicator = " ▲"

        classes: str = "cursor-pointer select-none hover:bg-muted/50"
        if is_active:
            classes += " font-bold"

        with t.sci_pro_table_head():
            t.span(
                f"{col_label}{indicator}",
                class_name=classes,
                on_click=lambda _e, k=col_key: self._on_sort_click(k),
            )
