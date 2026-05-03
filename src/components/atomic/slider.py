"""SciProSlider — PuePy atomic range slider with bind leak fix."""

from puepy import Component, Prop, t


@t.component()
class SciProSlider(Component):
    """Range slider input with min, max, step, value, and label.

    Uses Basecoat ``.slider`` class for styling. Includes the PuePy
    bind leak fix pattern for two-way binding via ``bind=`` prop.
    """

    component_name = "sci-pro-slider"

    _SLIDER_BASE = [
        "slider",
        "relative",
        "flex",
        "w-full",
        "touch-none",
        "select-none",
        "items-center",
        "h-6",
    ]
    _SLIDER_TRACK = [
        "relative",
        "h-2",
        "w-full",
        "grow",
        "overflow-hidden",
        "rounded-full",
        "bg-secondary",
        "dark:bg-slate-800",
        "border",
        "border-border",
        "pointer-events-none",
    ]
    _SLIDER_RANGE = [
        "absolute",
        "h-full",
        "bg-primary",
        "dark:bg-slate-200",
        "pointer-events-none",
    ]
    _SLIDER_THUMB = [
        "block",
        "h-5",
        "w-5",
        "rounded-full",
        "border-2",
        "border-primary",
        "bg-background",
        "shadow-sm",
        "ring-offset-background",
        "transition-colors",
        "pointer-events-none",
    ]

    props = [
        Prop("label", "Slider label text", str, ""),
        Prop("min", "Minimum value", float, 0.0),
        Prop("max", "Maximum value", float, 100.0),
        Prop("step", "Step increment", float, 1.0),
        Prop("value", "Current value", float, 0.0),
        Prop("disabled", "Disabled state", bool, False),
        Prop("class_name", "Additional Tailwind classes", str, None),
        Prop("show_value", "Display current value next to label", bool, False),
        Prop("on_input", "Input event handler", object, None),
    ]

    def __init__(self, *args, **kwargs):  # type: ignore[no-untyped-def]
        """Save bind key before PuePy processes it."""
        self._bind_key: str = kwargs.pop("bind", "")
        super().__init__(*args, **kwargs)

    def _handle_bind(self, kwargs: dict) -> None:  # type: ignore[override]
        """Intercept bind kwarg to prevent PuePy's built-in binding on redraw."""
        kwargs.pop("bind", None)
        self.bind = None

    def populate(self) -> None:
        """Render slider with track, range fill, and thumb."""
        label: str = self.props_values.get("label", "")
        min_val: float = self.props_values.get("min", 0.0)
        max_val: float = self.props_values.get("max", 100.0)
        step: float = self.props_values.get("step", 1.0)
        value: float = self.props_values.get("value", 0.0)
        disabled: bool = self.props_values.get("disabled", False)
        extra: str | None = self.props_values.get("class_name")
        show_value: bool = self.props_values.get("show_value", False)
        bind: str = self._bind_key

        # Use bind value if available, otherwise prop value.
        if bind:
            app_val: object = self.application.state.get(bind)
            if app_val is not None:
                value = float(app_val)  # type: ignore[arg-type]

        max_val = max(max_val, min_val + 1e-9)
        percentage: float = (value - min_val) / (max_val - min_val) * 100.0
        percentage = max(0.0, min(100.0, percentage))

        input_attrs: dict[str, object] = {
            "type": "range",
            "class_name": [
                "absolute",
                "inset-0",
                "w-full",
                "h-full",
                "opacity-0",
                "cursor-pointer",
                "z-30",
            ],
            "min": str(min_val),
            "max": str(max_val),
            "step": str(step),
            "value": str(value),
            "disabled": disabled,
        }

        # Pass through any extra attrs (like data-dimension)
        for k, v in self.attrs.items():
            if k not in input_attrs:
                input_attrs[k] = v

        on_input = self.props_values.get("on_input")

        if bind:
            input_attrs["on_input"] = self._on_input
        elif on_input:
            input_attrs["on_input"] = on_input

        wrapper_classes: list[str] = ["flex", "flex-col", "gap-2", "w-full"]
        if extra:
            wrapper_classes.append(extra)

        with t.div(class_name=wrapper_classes):
            if label or show_value:
                with t.div(class_name="flex items-center justify-between"):
                    if label:
                        with t.label(class_name="label text-sm font-medium text-foreground"):
                            t(label)
                    if show_value:
                        with t.span(class_name="text-sm font-mono text-primary"):
                            t(f"{value:.1f}" if value == float(int(value)) else str(value))

            with t.div(class_name=self._SLIDER_BASE):
                t.input(**input_attrs)
                with t.div(class_name=self._SLIDER_TRACK):
                    # Higher contrast background for dark mode track
                    with t.div(
                        class_name=self._SLIDER_RANGE,
                        style=f"width: {percentage}%",
                    ):
                        pass
                    # Thumb with better visibility
                    with t.div(
                        class_name=self._SLIDER_THUMB,
                        style=f"left: {percentage}%; transform: translateX(-50%);",
                    ):
                        pass

    def _on_input(self, event: object) -> None:
        """Sync slider value to application state."""
        bind: str = self._bind_key
        if bind:
            raw: str = event.target.value  # type: ignore[union-attr]
            self.application.state[bind] = float(raw)
            # Trigger optional on_input if provided
            on_input = self.props_values.get("on_input")
            if on_input:
                on_input(event)
