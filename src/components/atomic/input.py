"""SciProInput — PuePy atomic text input with bind leak fix, label, error, icons."""

from puepy import Component, Prop, t

_INPUT_BASE = [
    "input",
    "flex",
    "h-9",
    "w-full",
    "rounded-md",
    "border",
    "border-input",
    "bg-background",
    "px-3",
    "py-1",
    "text-sm",
    "shadow-sm",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-1",
    "focus-visible:ring-ring",
    "disabled:cursor-not-allowed",
    "disabled:opacity-50",
]


def _clamp_value(
    value: object,
    min_val: object = None,
    max_val: object = None,
) -> int | float | object:
    """Clamp a numeric value between min and max, preserving int type when possible."""
    try:
        numeric = float(value)  # type: ignore[arg-type]
    except (ValueError, TypeError):
        return value
    if min_val is not None:
        numeric = max(numeric, float(min_val))  # type: ignore[arg-type]
    if max_val is not None:
        numeric = min(numeric, float(max_val))  # type: ignore[arg-type]
    if isinstance(value, int) or (isinstance(value, str) and "." not in str(value)):
        return int(numeric)
    return numeric


@t.component()
class SciProInput(Component):
    """Full-featured text input with label, error state, and optional icon prefix/suffix.

    Supports two-way binding via ``bind=`` prop to ``self.application.state``.
    Includes the PuePy bind leak fix pattern in ``__init__`` and ``_handle_bind``.
    """

    enclosing_tag = "div"

    props = [
        Prop("label", "Input label text", str, ""),
        Prop("type", "HTML input type", str, "text"),
        Prop("placeholder", "Placeholder text", str, ""),
        Prop("min", "Minimum value (number inputs)", object, None),
        Prop("max", "Maximum value (number inputs)", object, None),
        Prop("step", "Step size (number inputs)", object, None),
        Prop("required", "Required field marker", bool, False),
        Prop("error", "Error state styling", bool, False),
        Prop("error_message", "Error text to display", str, "Invalid input"),
        Prop("disabled", "Disabled state", bool, False),
        Prop("icon_prefix", "Icon name before input", str, None),
        Prop("icon_suffix", "Icon name after input", str, None),
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
        """Render input with label, optional icons, and error display."""
        label: str = self.props_values.get("label", "")
        input_type: str = self.props_values.get("type", "text")
        bind: str = self._bind_key
        placeholder: str = self.props_values.get("placeholder", "")
        min_val: object = self.props_values.get("min")
        max_val: object = self.props_values.get("max")
        step: object = self.props_values.get("step")
        required: bool = self.props_values.get("required", False)
        error: bool = self.props_values.get("error", False)
        error_message: str = self.props_values.get("error_message", "Invalid input")
        disabled: bool = self.props_values.get("disabled", False)
        icon_prefix: str | None = self.props_values.get("icon_prefix")
        icon_suffix: str | None = self.props_values.get("icon_suffix")

        classes: list[str] = list(_INPUT_BASE)

        if error:
            classes = [
                "border-destructive"
                if c == "border-input"
                else "focus-visible:ring-destructive"
                if c == "focus-visible:ring-ring"
                else c
                for c in classes
            ]

        if icon_prefix:
            classes.append("pl-9")
        if icon_suffix:
            classes.append("pr-9")

        extra_classes = self.attrs.get("class_name", "")
        input_attrs: dict[str, object] = {"type": input_type, "class_name": classes + [extra_classes]}

        if placeholder:
            input_attrs["placeholder"] = placeholder
        if required:
            input_attrs["required"] = required
        if disabled:
            input_attrs["disabled"] = disabled

        error_id = f"input-error-{id(self)}"
        if error:
            input_attrs["aria-invalid"] = "true"
            input_attrs["aria-describedby"] = error_id

        if input_type == "number":
            if min_val is not None:
                input_attrs["min"] = min_val
            if max_val is not None:
                input_attrs["max"] = max_val
            if step is not None:
                input_attrs["step"] = step

        if bind:
            input_attrs.update(self._bind_attrs(bind, input_type))

        # Pass through any extra attrs (like data-dimension)
        for k, v in self.attrs.items():
            if k not in input_attrs:
                input_attrs[k] = v

        if label:
            with t.label(class_name="label block text-sm font-medium text-foreground mb-1.5"):
                t(label)
                if required:
                    with t.span(class_name="text-destructive ml-0.5"):
                        t("*")

        has_icon = icon_prefix or icon_suffix
        if has_icon:
            with t.div(class_name="relative flex items-center w-full"):
                if icon_prefix:
                    t.sci_pro_icon(
                        name=icon_prefix,
                        size="sm",
                        class_name="absolute left-3 text-muted-foreground",
                    )
                t.input(**input_attrs)
                if icon_suffix:
                    t.sci_pro_icon(
                        name=icon_suffix,
                        size="sm",
                        class_name="absolute right-3 text-muted-foreground",
                    )
        else:
            t.input(**input_attrs)

        if error:
            with t.p(
                id=error_id,
                class_name="text-xs text-destructive mt-1",
            ):
                t(error_message)

    def _bind_attrs(self, bind: str, input_type: str) -> dict[str, object]:
        """Build attrs dict for value binding + event handlers."""
        app_state = self.application.state
        value: object = app_state.get(bind, "")
        attrs: dict[str, object] = {
            "value": value,
            "on_input": self._on_input,
        }
        if input_type == "number":
            attrs["on_blur"] = self._on_blur_clamp
        return attrs

    def _on_input(self, event: object) -> None:
        """Sync input value to application state on each keystroke."""
        bind: str = self._bind_key
        if bind:
            self.application.state[bind] = event.target.value  # type: ignore[union-attr]

    def _on_blur_clamp(self, event: object) -> None:  # noqa: ARG002
        """Clamp numeric value to min/max bounds on blur."""
        bind: str = self._bind_key
        min_val: object = self.props_values.get("min")
        max_val: object = self.props_values.get("max")
        try:
            current: object = self.application.state[bind]
        except (KeyError, TypeError):
            return
        clamped: object = _clamp_value(current, min_val, max_val)
        if clamped != current:
            self.application.state[bind] = clamped
