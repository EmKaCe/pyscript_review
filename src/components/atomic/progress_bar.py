"""SciProProgressBar — PuePy atomic progress indicator component."""

from puepy import Component, Prop, t


@t.component()
class SciProProgressBar(Component):
    """Progress bar component using native ``<progress>`` or div-based rendering.

    Uses Basecoat ``.progress`` class with Tailwind v4 extensions.
    """

    component_name = "sci-progress-bar"

    _PROGRESS_BASE = [
        "bg-secondary",
        "relative",
        "h-2",
        "w-full",
        "overflow-hidden",
        "rounded-full",
    ]
    _PROGRESS_INDICATOR = [
        "h-full",
        "w-full",
        "flex-1",
        "transition-all",
    ]

    props = [
        Prop("value", "Current progress value", float, 0.0),
        Prop("max", "Maximum progress value", float, 100.0),
        Prop("label", "Accessible label for progress", str, ""),
        Prop("class_name", "Additional Tailwind classes", str, None),
        Prop("indicator_class", "Custom classes for the moving part", str, None),
        Prop("show_label", "Show text label next to bar", bool, False),
    ]

    def populate(self) -> None:
        """Render a progress bar with value indicator."""
        value: float = self.props_values.get("value", 0.0)
        max_val: float = self.props_values.get("max", 100.0)
        label: str = self.props_values.get("label", "")
        extra: str | None = self.props_values.get("class_name")
        indicator_extra: str | None = self.props_values.get("indicator_class")
        show_label: bool = self.props_values.get("show_label", False)

        # Calculate percentage for width and clamping.
        max_val = max(max_val, 0.001)
        percentage = min(max(value / max_val * 100.0, 0.0), 100.0)

        bar_color = "bg-primary"
        
        wrapper_classes: list[str] = ["flex", "flex-col", "gap-1.5", "w-full"]

        if show_label and label:
            with t.div(class_name=wrapper_classes):
                with t.div(class_name="flex items-center justify-between"):
                    with t.span(class_name="text-sm font-medium text-foreground"):
                        t(label)
                    with t.span(class_name="text-sm text-muted-foreground"):
                        t(f"{percentage:.0f}%")

                bar_classes = list(self._PROGRESS_BASE)
                if extra:
                    bar_classes.append(extra)

                with t.div(
                    class_name=bar_classes,
                    role="progressbar",
                    aria_valuenow=str(value),
                    aria_valuemax=str(max_val),
                    aria_valuemin="0",
                    aria_label=label or "Progress",
                ):
                    indicator_classes = [bar_color] + list(self._PROGRESS_INDICATOR)
                    if indicator_extra:
                        indicator_classes.append(indicator_extra)
                    with t.div(
                        class_name=indicator_classes,
                        style=f"transform: translateX(-{100 - percentage}%)",
                    ):
                        pass
        else:
            bar_classes = list(self._PROGRESS_BASE)
            if extra:
                bar_classes.append(extra)

            aria_kwargs: dict[str, object] = {
                "class_name": bar_classes,
                "role": "progressbar",
                "aria_valuenow": str(value),
                "aria_valuemax": str(max_val),
                "aria_valuemin": "0",
            }
            if label:
                aria_kwargs["aria_label"] = label

            with t.div(**aria_kwargs):  # noqa: SIM117
                indicator_classes = [bar_color] + list(self._PROGRESS_INDICATOR)
                if indicator_extra:
                    indicator_classes.append(indicator_extra)
                with t.div(
                    class_name=indicator_classes,
                    style=f"transform: translateX(-{100 - percentage}%)",
                ):
                    pass
