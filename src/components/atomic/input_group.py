"""SciProInputGroup — PuePy atomic input group with fixed prefix label.

Renders a horizontal group consisting of a read-only prefix span and a text input,
with an optional label above and error/helper text below.
"""

from puepy import Component, Prop, t

_PREFIX_SPAN = [
    "inline-flex",
    "items-center",
    "rounded-l-md",
    "border",
    "border-r-0",
    "border-input",
    "bg-muted",
    "px-3",
    "py-2",
    "text-sm",
    "font-medium",
    "tabular-nums",
]

_INPUT_CLASSES = [
    "flex",
    "h-10",
    "w-full",
    "rounded-r-md",
    "rounded-l-none",
    "border",
    "border-input",
    "bg-background",
    "px-3",
    "py-2",
    "text-sm",
    "text-foreground",
    "placeholder:text-muted-foreground",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-ring",
    "focus-visible:ring-offset-2",
]


@t.component()
class SciProInputGroup(Component):
    """Input group with a fixed prefix label and text input.

    Supports two-way binding via ``bind=`` prop to ``self.application.state``.
    The prefix is display-only; the bound state key stores only the
    user-entered portion.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-input-group"

    props = [
        Prop("label", "Label text displayed above the input group", str, ""),
        Prop("prefix", "Fixed readonly prefix displayed before the input", str, ""),
        Prop("placeholder", "Placeholder text for the text input", str, ""),
        Prop("error", "Error text displayed below the input group", str, ""),
        Prop("helper_text", "Helper text displayed below the input group", str, ""),
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
        """Render label, prefix+input group, error, and helper text."""
        label: str = self.props_values.get("label", "")
        prefix: str = self.props_values.get("prefix", "")
        placeholder: str = self.props_values.get("placeholder", "")
        error: str = self.props_values.get("error", "")
        helper_text: str = self.props_values.get("helper_text", "")
        bind: str = self._bind_key

        # Label
        if label:
            with t.label(
                class_name="text-sm font-medium text-foreground block mb-1.5",
            ):
                t(label)

        # Input group: prefix span + text input
        with t.div(class_name="flex items-center gap-0"):
            with t.span(class_name=_PREFIX_SPAN):
                t(prefix)

            input_attrs: dict[str, object] = {
                "type": "text",
                "class_name": _INPUT_CLASSES,
                "on_input": self._on_input,
            }
            if placeholder:
                input_attrs["placeholder"] = placeholder
            if bind:
                input_attrs["value"] = self.application.state.get(bind, "")

            t.input(**input_attrs)

        # Error text
        if error:
            with t.p(class_name="text-xs text-destructive mt-1"):
                t(error)

        # Helper text
        if helper_text:
            with t.p(class_name="text-xs text-muted-foreground mt-1"):
                t(helper_text)

    def _on_input(self, event: object) -> None:
        """Sync input value to application state, stripping prefix if present."""
        bind: str = self._bind_key
        if not bind:
            return
        value: object = event.target.value  # type: ignore[union-attr]
        prefix: str = self.props_values.get("prefix", "")
        if prefix and isinstance(value, str) and value.startswith(prefix):
            value = value[len(prefix) :]
        self.application.state[bind] = value
