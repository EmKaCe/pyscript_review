"""SciProGradingSidebar — Feature component for the review grading interface.

Provides a sidebar containing grading dimension sliders, a real-time grade result
card with fence warnings, and per-dimension progress bars.
"""

from __future__ import annotations

from puepy import Component, t

from src.services.grade_calculator import calculate_grade
from src.services.grading_config import DEFAULT_GRADING_CONFIG, weight_percentage
from src.utils.grade_colors import sidebar_grade_color_config


@t.component()
class SciProGradingSidebar(Component):
    """Right sidebar with dimension sliders and German grade result."""

    component_name = "sci-pro-grading-sidebar"
    redraw_on_app_state_changes = ["grading_inputs", "grade_result"]

    def _get_grade_label(self, grade: float) -> str:
        if grade <= 1.7:
            return "Excellent"
        if grade <= 2.7:
            return "Good"
        if grade <= 3.7:
            return "Satisfactory"
        return "Insufficient"

    def on_ready(self) -> None:
        """Calculate initial grade on mount."""
        self._recalculate()

    def _recalculate(self) -> None:
        inputs = self.application.state.get("grading_inputs")
        if inputs:
            try:
                res = calculate_grade(inputs, DEFAULT_GRADING_CONFIG)
                self.application.state["grade_result"] = res
            except Exception:
                pass

    def populate(self) -> None:
        """Render the grading sidebar content."""
        grading_inputs = self.application.state.get("grading_inputs")
        grade_result = self.application.state.get("grade_result")

        # If we have inputs but no result, calculate it now
        if grading_inputs and not grade_result:
            try:
                grade_result = calculate_grade(grading_inputs, DEFAULT_GRADING_CONFIG)
                self.application.state["grade_result"] = grade_result
            except Exception:
                pass

        scores = grading_inputs.scores if hasattr(grading_inputs, "scores") else (grading_inputs or {})

        with t.aside(class_name="flex flex-col gap-5 w-full lg:w-80 lg:min-w-80"):
            # Grading Dimensions Card
            with t.sci_pro_card():
                with t.sci_pro_card_header(class_name="pb-3"):
                    t.sci_pro_card_title("Grading", class_name="text-base")

                with t.sci_pro_card_content(class_name="space-y-4"):
                    for dim in DEFAULT_GRADING_CONFIG.dimensions:
                        val = float(scores.get(dim.name, 0.0))
                        weight = weight_percentage(dim.name, DEFAULT_GRADING_CONFIG)

                        with t.div(class_name="space-y-1.5"):
                            with t.div(class_name="flex items-center justify-between"):
                                with t.div(class_name="flex items-center gap-1.5 min-w-0"):
                                    label = dim.name.replace("_", " ").title()
                                    if "Design" in label:
                                        label = label.replace("Design", "& Design")
                                    t.label(label, class_name="text-xs font-medium truncate")
                                    t.sci_pro_badge(
                                        variant="secondary",
                                        label=f"{weight:.0f}%",
                                        class_name="px-1 py-px text-[10px] font-semibold tabular-nums shrink-0 rounded-full"
                                    )
                                with t.span(class_name="text-xs font-semibold tabular-nums shrink-0 ml-2"):
                                    t(f"{val:.1f}")
                                    t.span(f"/{dim.max_points}", class_name="text-muted-foreground font-normal")

                            with t.div(class_name="flex gap-2 items-center"):
                                t.sci_pro_input(
                                    type="number",
                                    min=0.0,
                                    max=float(dim.max_points),
                                    step=0.5,
                                    value=val,
                                    on_input=self._on_number_input,
                                    data_dimension=dim.name,
                                    class_name="h-8 py-0 px-2 text-right tabular-nums w-24"
                                )
                                with t.div(class_name="flex-1"):
                                    pct = (val / dim.max_points) * 100.0
                                    bar_color = self._get_bar_color(pct)
                                    t.sci_pro_progress_bar(
                                        value=pct,
                                        class_name="h-1.5",
                                        indicator_class=bar_color
                                    )

            # Result Card
            if grade_result:
                r = grade_result
                near_fence = (r.points_to_next_grade is not None and r.points_to_next_grade <= 5) or r.points_above_current_grade <= 2

                with t.sci_pro_card():
                    with t.sci_pro_card_header(class_name="pb-3 text-center"):
                        t.sci_pro_card_title("Result", class_name="text-base")

                    with t.sci_pro_card_content(class_name="space-y-4"):
                        # Grade Pill
                        with t.div(class_name="flex flex-col items-center gap-1 py-2"):
                            color_config = sidebar_grade_color_config(r.grade)
                            color_cls = f"{color_config['bg_class']} {color_config['text_class']} {color_config['border_class']}"
                            with t.div(class_name=f"rounded-2xl px-8 py-5 text-center shadow-sm {color_cls}"):
                                t.span(f"{r.grade:.1f}", class_name="text-5xl font-extrabold tabular-nums leading-none tracking-tighter")
                                t.div(self._get_grade_label(r.grade), class_name="mt-2 text-[10px] font-bold uppercase tracking-widest opacity-80")
                            t.span(f"US Equivalent: {r.us_equivalent}", class_name="text-xs font-bold text-muted-foreground mt-2")

                        # Overall Progress
                        with t.div(class_name="space-y-1.5"):
                            with t.div(class_name="flex items-center justify-between text-xs tabular-nums"):
                                t.span("Overall", class_name="text-muted-foreground font-medium")
                                t.span(f"{r.percentage:.1f}%", class_name="font-bold")
                            t.sci_pro_progress_bar(value=r.percentage, class_name="h-2")

                        # Near-fence warning
                        if near_fence:
                            with t.div(class_name="rounded-lg border border-dashed border-amber-300 dark:border-amber-700 bg-amber-50/50 dark:bg-amber-950/20 px-3 py-2"):
                                with t.div(class_name="space-y-1 text-xs tabular-nums"):
                                    if r.points_to_next_grade is not None and r.points_to_next_grade <= 5:
                                        with t.div(class_name="flex items-center gap-1.5 text-amber-800 dark:text-amber-300"):
                                            t.i(class_name="i-lucide-trending-up size-3 shrink-0")
                                            with t.span():
                                                t.strong(f"+{r.points_to_next_grade:.1f}%")
                                                t(" to next grade")
                                    if r.points_above_current_grade <= 2 and r.grade < 5.0:
                                        with t.div(class_name="flex items-center gap-1.5 text-amber-800 dark:text-amber-300"):
                                            t.i(class_name="i-lucide-alert-triangle size-3 shrink-0")
                                            with t.span():
                                                t.strong(f"{r.points_above_current_grade:.1f}%")
                                                t(" above boundary")

                        t.sci_pro_separator()

                        # Dimension Breakdown
                        with t.div(class_name="space-y-3"):
                            for d in r.per_dimension:
                                pct = d.percentage
                                bar_color = self._get_bar_color(pct)
                                with t.div(class_name="space-y-1.5"):
                                    with t.div(class_name="flex items-center justify-between text-[10px]"):
                                        label = d.name.replace("_", " ").title()
                                        if "Design" in label:
                                            label = label.replace("Design", "& Design")
                                        t.span(label, class_name="text-muted-foreground font-medium truncate max-w-[140px]")
                                        t.span(f"{d.score:.1f}/{d.max_points}", class_name="font-bold tabular-nums")
                                    t.sci_pro_progress_bar(
                                        value=pct,
                                        class_name="h-1.5",
                                        indicator_class=bar_color
                                    )

    def _get_bar_color(self, pct: float) -> str:
        """Return a solid Tailwind color class based on percentage."""
        if pct >= 85:  # 1.0 - 1.7
            return "bg-emerald-500"
        if pct >= 70:  # 2.0 - 2.7
            return "bg-blue-500"
        if pct >= 55:  # 3.0 - 3.7
            return "bg-violet-500"
        if pct >= 50:  # 4.0
            return "bg-amber-500"
        return "bg-red-500"

    def _on_number_input(self, event: object) -> None:
        """Handle input from numeric input."""
        try:
            dim_name = event.target.getAttribute("data-dimension")
            val = float(event.target.value)
            self._on_input(dim_name, val)
        except (AttributeError, ValueError, TypeError):
            pass

    def _on_input(self, dim_name: str, value: float) -> None:
        self.trigger_event("grading-change", detail={"dimension": dim_name, "value": value})

    def on_grading_inputs_change(self, _value: object) -> None:
        """Auto-recalculate when global state changes."""
        self._recalculate()
