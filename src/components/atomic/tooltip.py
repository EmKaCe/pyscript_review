"""SciProTooltip — PuePy atomic CSS tooltip using Basecoat data-tooltip pattern."""

from puepy import Component, Prop, t


@t.component()
class SciProTooltip(Component):
    """Wraps content and shows a tooltip on hover/focus.

    Uses CSS ``group-hover`` / ``group-focus-within`` pattern for
    visibility toggling. Can also use Basecoat ``data-tooltip`` attribute
    when the text fits within an attribute.
    """

    enclosing_tag = "span"
    component_name = "sci-pro-tooltip"

    _WRAPPER_CLASSES = ["relative", "inline-block", "group"]

    _TOOLTIP_BASE = [
        "absolute",
        "z-50",
        "invisible",
        "opacity-0",
        "group-hover:visible",
        "group-hover:opacity-100",
        "group-focus-within:visible",
        "group-focus-within:opacity-100",
        "transition-opacity",
        "duration-200",
        "text-xs",
        "text-popover-foreground",
        "bg-popover",
        "rounded-md",
        "px-2",
        "py-1",
        "shadow-md",
        "whitespace-nowrap",
        "pointer-events-none",
    ]

    _POSITION_CLASSES: dict[str, list[str]] = {
        "top": ["bottom-full", "left-1/2", "-translate-x-1/2", "mb-2"],
        "bottom": ["top-full", "left-1/2", "-translate-x-1/2", "mt-2"],
        "left": ["right-full", "top-1/2", "-translate-y-1/2", "mr-2"],
        "right": ["left-full", "top-1/2", "-translate-y-1/2", "ml-2"],
    }

    props = [
        Prop("content", "Tooltip text to display", str, ""),
        Prop("position", "Tooltip position: top, bottom, left, right", str, "top"),
        Prop("class_name", "Additional Tailwind classes for wrapper", str, None),
    ]

    def populate(self) -> None:
        """Render tooltip wrapper with hidden overlay content."""
        content: str = self.props_values.get("content", "")
        position: str = self.props_values.get("position", "top")
        extra: str | None = self.props_values.get("class_name")

        tooltip_id = f"sci-pro-tooltip-{id(self)}"

        wrapper_classes: list[str] = list(self._WRAPPER_CLASSES)
        if extra:
            wrapper_classes.append(extra)

        tooltip_classes = list(self._TOOLTIP_BASE)
        tooltip_classes.extend(self._POSITION_CLASSES.get(position, self._POSITION_CLASSES["top"]))

        with t.span(
            class_name=wrapper_classes,
            aria_describedby=tooltip_id,
        ):
            t.call()
            with t.span(
                class_name=tooltip_classes,
                role="tooltip",
                id=tooltip_id,
                aria_hidden="true",
            ):
                t(content)
