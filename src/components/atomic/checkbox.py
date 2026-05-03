"""SciProCheckbox — PuePy atomic checkbox with label and on_change handler."""

from puepy import Component, Prop, t


@t.component()
class SciProCheckbox(Component):
    """Checkbox component with label and change callback.

    Does NOT use ``bind=`` PuePy built-in binding — uses explicit
    ``on_change`` handler instead, so no bind leak fix is needed.
    """

    component_name = "sci-pro-checkbox"

    _CB_WRAPPER = ["flex", "items-center", "gap-2"]
    _CB_INPUT_BASE = [
        "peer",
        "h-4",
        "w-4",
        "shrink-0",
        "rounded",
        "border",
        "border-primary",
        "ring-offset-background",
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-ring",
        "focus-visible:ring-offset-2",
        "disabled:cursor-not-allowed",
        "disabled:opacity-50",
    ]
    _CB_LABEL = [
        "text-sm",
        "font-medium",
        "leading-none",
        "peer-disabled:cursor-not-allowed",
        "peer-disabled:opacity-70",
    ]

    props = [
        Prop("label", "Label text for checkbox", str, ""),
        Prop("checked", "Checked state", bool, False),
        Prop("disabled", "Disabled state", bool, False),
        Prop("error", "Error state styling", bool, False),
        Prop("on_change", "Callback for state change (receives new boolean)", object, None),
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]

    def populate(self) -> None:
        """Render checkbox with label and change handler."""
        label: str = self.props_values.get("label", "")
        checked_val: bool = self.props_values.get("checked", False)
        disabled: bool = self.props_values.get("disabled", False)
        error: bool = self.props_values.get("error", False)
        on_change: object = self.props_values.get("on_change")
        extra: str | None = self.props_values.get("class_name")

        wrapper_classes: list[str] = list(self._CB_WRAPPER)
        input_classes: list[str] = list(self._CB_INPUT_BASE)
        label_classes: list[str] = list(self._CB_LABEL)

        if error:
            input_classes.append("border-destructive")
        if extra:
            wrapper_classes.append(extra)

        input_attrs: dict[str, object] = {
            "type": "checkbox",
            "class_name": input_classes,
            "checked": checked_val,
            "disabled": disabled,
        }
        if on_change is not None:
            input_attrs["on_change"] = on_change
        if error:
            input_attrs["aria-invalid"] = "true"

        with t.div(class_name=wrapper_classes):
            t.input(**input_attrs)
            if label:
                with t.label(class_name=label_classes):
                    t(label)
