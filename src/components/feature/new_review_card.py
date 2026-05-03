"""SciProNewReviewCard — Feature component for starting a new review session.

Provides a form with a split student ID input (semester prefix + number),
assignment selection, and validation before navigating to the review page.
Matches the svelte new-review-card design exactly.
"""

import re

from puepy import Component, t

from src.utils.semester import get_current_semester, parse_semester


def _build_semester_info() -> tuple[str, str]:
    """Build the semester prefix and human-readable label.

    Returns:
        Tuple of (prefix, label), e.g. ("2026SS_", "Sommersemester 2026").
    """
    sem = get_current_semester()
    parsed = parse_semester(sem)

    if parsed is None:
        return (f"20{sem[2:]}{sem[:2]}_", sem)

    season, year = parsed
    if season == "SS":
        prefix = f"{year}SS_"
        label = f"Sommersemester {year}"
    else:
        prefix = f"{year}WS_"
        label = f"Wintersemester {year}/{year + 1}"

    return (prefix, label)


_STUDENT_NUMBER_RE = re.compile(r"^\d{1,6}$")


@t.component()
class SciProNewReviewCard(Component):
    """Card to initiate a new review session.

    Registered as ``t.sci_pro_new_review_card()``.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-new-review-card"

    redraw_on_app_state_changes = ["student_id"]

    def initial(self) -> dict:
        """Local UI state for the component."""
        return {
            "error": "",
        }

    def populate(self) -> None:
        """Render the new review form matching the svelte reference design."""
        assignments: list[dict] = self.application.state.get("assignments", [])
        semester_prefix, semester_label = _build_semester_info()
        error: str = self.state.get("error", "")

        assignment_options = [(a["id"], a["name"]) for a in assignments if a.get("enabled", True)]

        with t.sci_pro_card(class_name="hover:shadow-md transition-shadow"):
            with t.sci_pro_card_header(class_name="flex flex-row items-center gap-3"):
                with t.div(
                    class_name="h-10 w-10 rounded-lg bg-primary/10 text-primary"
                    " flex items-center justify-center"
                ):
                    t.sci_pro_icon(name="plus", size="md")
                with t.div(class_name="flex flex-col gap-1"):
                    with t.sci_pro_card_title(class_name="text-base"):
                        t("New Review")
                    with t.sci_pro_card_description():
                        t("Start a fresh peer review")

            with t.sci_pro_card_content():
                # Suppress error while user is typing
                display_error = (
                    "" if self.application.state.get("student_id", "").strip() else error
                )

                t.sci_pro_input_group(
                    label="Student ID",
                    prefix=semester_prefix,
                    placeholder="12345",
                    bind="student_id",
                    error=display_error,
                    helper_text=f"{semester_label} — enter your number only",
                )

                with t.div(class_name="flex flex-col gap-1.5"):
                    t.sci_pro_select(
                        label="Assignment",
                        options=assignment_options,
                        placeholder="Select assignment...",
                        bind="assignment_id",
                    )

                t.sci_pro_button(
                    variant="primary",
                    label="Start Review",
                    on_click=self._on_start_review,
                    class_name="w-full",
                )

    def _on_start_review(self, _event: object = None) -> None:
        """Validate inputs, compose full student ID, and navigate to review."""
        student_number: str = self.application.state.get("student_id", "").strip()
        assignment_id: str = self.application.state.get("assignment_id", "")

        # Validate student number: 1-6 digits only
        if not _STUDENT_NUMBER_RE.match(student_number):
            self.state["error"] = "Student number must be 1–6 digits."
            return

        semester_prefix, _ = _build_semester_info()
        # Pad to at least 2 digits: "5" → "05", "123" → "123"
        padded = student_number.zfill(2)
        full_id = f"{semester_prefix}{padded}"

        if not assignment_id:
            self.state["error"] = "Please select an assignment."
            return

        self.application.state["student_id"] = full_id
        self.application.state["assignment_id"] = assignment_id

        from src.services.criteria_loader import get_criteria_for_assignment

        bundle = get_criteria_for_assignment(assignment_id)
        self.application.state["criteria_bundle"] = bundle

        self.application.router.navigate_to_path("/review")
