"""SciProSelect — PuePy atomic dropdown select with bind leak fix."""

from puepy import Component, Prop, t

_SELECT_BASE = [
    "flex",
    "h-10",
    "w-full",
    "rounded-md",
    "border",
    "border-input",
    "bg-background",
    "px-3",
    "py-2",
    "text-sm",
    "text-foreground",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-ring",
    "focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed",
    "disabled:opacity-50",
    "appearance-none",
    "bg-[length:16px]",
    "bg-[right_0.5rem_center]",
    "bg-no-repeat",
    "pr-10",
]


@t.component()
class SciProSelect(Component):
    """Dropdown select with label, options list, and error state.

    Includes the PuePy bind leak fix pattern. Options are passed as
    a list of ``(value, label)`` tuples.
    """

    enclosing_tag = "div"

    props = [
        Prop("label", "Select label text", str, ""),
        Prop("options", "List of (value, label) tuples", list, ()),
        Prop("placeholder", "Placeholder prompt text", str, ""),
        Prop("required", "Required field marker", bool, False),
        Prop("error", "Error state styling", bool, False),
        Prop("error_message", "Error text to display", str, "Invalid input"),
        Prop("disabled", "Disabled state", bool, False),
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
        """Render select with label, options, and optional error display."""
        label: str = self.props_values.get("label", "")
        options: list[tuple[str, str]] = self.props_values.get("options", [])
        placeholder: str = self.props_values.get("placeholder", "")
        required: bool = self.props_values.get("required", False)
        error: bool = self.props_values.get("error", False)
        error_message: str = self.props_values.get("error_message", "Invalid input")
        disabled: bool = self.props_values.get("disabled", False)
        bind: str = self._bind_key

        classes: list[str] = list(_SELECT_BASE)

        if error:
            classes = [
                "border-destructive"
                if c == "border-input"
                else "focus-visible:ring-destructive"
                if c == "focus-visible:ring-ring"
                else c
                for c in classes
            ]

        select_attrs: dict[str, object] = {"class_name": classes}

        if placeholder:
            select_attrs["placeholder"] = placeholder
        if required:
            select_attrs["required"] = required
        if disabled:
            select_attrs["disabled"] = disabled

        error_id = f"select-error-{id(self)}"
        if error:
            select_attrs["aria-invalid"] = "true"
            select_attrs["aria-describedby"] = error_id

        if bind:
            select_attrs.update(self._bind_attrs(bind))

        if label:
            with t.label(class_name="label block text-sm font-medium text-foreground mb-1.5"):
                t(label)
                if required:
                    with t.span(class_name="text-destructive ml-0.5"):
                        t("*")

        with t.select(**select_attrs):
            if placeholder:
                with t.option(value="", disabled=True, selected=True):
                    t(placeholder)
            for val, lbl in options:
                with t.option(value=val):
                    t(lbl)

        if error:
            with t.p(
                id=error_id,
                class_name="text-xs text-destructive mt-1",
            ):
                t(error_message)

    def _bind_attrs(self, bind: str) -> dict[str, object]:
        """Build attrs dict for value binding + on_change handler."""
        app_state = self.application.state
        value: object = app_state.get(bind, "")
        return {"value": value, "on_change": self._on_change}

    def _on_change(self, event: object) -> None:
        """Sync select value to application state on change."""
        bind: str = self._bind_key
        if bind:
            self.application.state[bind] = event.target.value  # type: ignore[union-attr]
