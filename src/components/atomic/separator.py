"""SciProSeparator — PuePy atomic horizontal/vertical divider component."""

from puepy import Component, Prop, t


@t.component()
class SciProSeparator(Component):
    """Horizontal or vertical separator/divider.

    Uses CSS ``border`` for the visual line. Orientation controls layout.
    """

    component_name = "sci-pro-separator"

    _HORIZONTAL_CLASSES = [
        "h-px",
        "w-full",
        "shrink-0",
        "bg-border",
    ]
    _VERTICAL_CLASSES = [
        "h-full",
        "w-px",
        "shrink-0",
        "bg-border",
    ]

    props = [
        Prop("orientation", "Orientation: horizontal or vertical", str, "horizontal"),
        Prop("class_name", "Additional Tailwind classes", str, None),
        Prop("decorative", "Whether separator is decorative (no role)", bool, True),
    ]

    def populate(self) -> None:
        """Render a horizontal or vertical separator line."""
        orientation: str = self.props_values.get("orientation", "horizontal")
        extra: str | None = self.props_values.get("class_name")
        decorative: bool = self.props_values.get("decorative", True)

        is_horizontal = orientation != "vertical"
        classes = list(self._HORIZONTAL_CLASSES) if is_horizontal else list(self._VERTICAL_CLASSES)
        if extra:
            classes.append(extra)

        attrs: dict[str, object] = {"class_name": classes}
        if decorative:
            attrs["role"] = "none"
        else:
            attrs["role"] = "separator"

        with t.div(**attrs):
            pass
