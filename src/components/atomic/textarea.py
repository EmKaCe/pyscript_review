"""SciProTextarea — PuePy atomic multiline text input with bind leak fix."""

from puepy import Component, Prop, t

_TEXTAREA_BASE = [
    "textarea",
    "flex",
    "min-h-[80px]",
    "w-full",
    "rounded-md",
    "border",
    "border-input",
    "bg-background",
    "px-3",
    "py-2",
    "text-sm",
    "text-foreground",
    "placeholder:text-muted-foreground",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-ring",
    "focus-visible:ring-offset-2",
    "disabled:cursor-not-allowed",
    "disabled:opacity-50",
]

_RESIZE_CLASSES: dict[str, str] = {
    "none": "resize-none",
    "vertical": "resize-y",
    "horizontal": "resize-x",
    "both": "resize",
}


@t.component()
class SciProTextarea(Component):
    """Multiline text input with label, error state, character counter, and bind support.

    Includes the PuePy bind leak fix pattern.
    """

    enclosing_tag = "div"

    props = [
        Prop("label", "Textarea label text", str, ""),
        Prop("placeholder", "Placeholder text", str, ""),
        Prop("rows", "Number of visible rows", int, None),
        Prop("cols", "Number of visible columns", int, None),
        Prop("readonly", "Read-only state", bool, False),
        Prop("max_length", "Maximum character count", int, None),
        Prop("error", "Error state styling", bool, False),
        Prop("error_message", "Error text to display", str, "Invalid input"),
        Prop("resize", "Resize behavior: none, vertical, horizontal, both", str, "vertical"),
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
        """Render textarea with optional label, error, and character counter."""
        label: str = self.props_values.get("label", "")
        bind: str = self._bind_key
        placeholder: str = self.props_values.get("placeholder", "")
        rows: int | None = self.props_values.get("rows")
        cols: int | None = self.props_values.get("cols")
        readonly: bool = self.props_values.get("readonly", False)
        max_length: int | None = self.props_values.get("max_length")
        error: bool = self.props_values.get("error", False)
        error_message: str = self.props_values.get("error_message", "Invalid input")
        resize: str = self.props_values.get("resize", "vertical")

        classes: list[str] = list(_TEXTAREA_BASE)

        if readonly:
            classes = [c for c in classes if c not in ("bg-background",)]
            classes.extend(["bg-muted", "cursor-default"])

        if error:
            classes = [
                "border-destructive"
                if c == "border-input"
                else "focus-visible:ring-destructive"
                if c == "focus-visible:ring-ring"
                else c
                for c in classes
            ]

        resize_cls: str = _RESIZE_CLASSES.get(resize, "resize-y")
        classes.append(resize_cls)

        textarea_attrs: dict[str, object] = {"class_name": classes}

        if placeholder:
            textarea_attrs["placeholder"] = placeholder
        if rows is not None:
            textarea_attrs["rows"] = rows
        if cols is not None:
            textarea_attrs["cols"] = cols
        if readonly:
            textarea_attrs["readonly"] = True
        if max_length is not None:
            textarea_attrs["maxlength"] = max_length
        if error:
            textarea_attrs["aria-invalid"] = "true"
            textarea_attrs["aria-describedby"] = f"{bind or 'ta'}-error"

        if bind:
            textarea_attrs.update(self._bind_attrs(bind))

        if label:
            with t.label(class_name="label block text-sm font-medium text-foreground mb-1.5"):
                t(label)

        t.textarea(**textarea_attrs)

        if max_length is not None:
            current_len: int = len(self.application.state.get(bind, "")) if bind else 0
            indicator_classes: list[str] = ["text-xs", "mt-1", "text-right"]
            if current_len >= max_length:
                indicator_classes.append("text-destructive")
            else:
                indicator_classes.append("text-muted-foreground")
            with t.p(class_name=indicator_classes):
                t(f"{current_len}/{max_length}")

        if error:
            with t.p(class_name="text-xs text-destructive mt-1"):
                t(error_message)

    def _bind_attrs(self, bind: str) -> dict[str, object]:
        """Build attrs dict for value binding + on_input handler."""
        app_state = self.application.state
        value: object = app_state.get(bind, "")
        return {"value": value, "on_input": self._on_input}

    def _on_input(self, event: object) -> None:
        """Sync textarea value to application state on each keystroke."""
        bind: str = self._bind_key
        if bind:
            self.application.state[bind] = event.target.value  # type: ignore[union-attr]
