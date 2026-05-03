"""SciProPopover — PuePy composite wrapping Basecoat .popover JS."""

from puepy import Component, Prop, t

_TRIGGER_BASE = [
    "btn",
    "btn-outline",
    "h-10",
    "px-4",
    "py-2",
    "text-sm",
    "font-medium",
    "inline-flex",
    "items-center",
    "gap-2",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-ring",
    "focus-visible:ring-offset-2",
]

_POPOVER_CONTENT = [
    "absolute",
    "z-50",
    "w-72",
    "rounded-md",
    "border",
    "bg-popover",
    "text-popover-foreground",
    "shadow-md",
    "p-4",
    "mt-2",
]


@t.component()
class SciProPopover(Component):
    """Small overlay anchored to a trigger button using Basecoat ``.popover``.

    Uses Basecoat JS for open/close, keyboard (Escape), outside-click
    dismiss, and ``basecoat:popover`` event coordination.

    ``content`` prop can be a string (rendered as text) or HTML.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-popover"

    default_classes = ["popover", "relative", "inline-block"]

    props = [
        Prop("trigger_label", "Button label for the popover trigger", str, "Open"),
        Prop("content", "Popover content text or HTML", str, ""),
        Prop("position", "Popover position: top, bottom, left, right", str, "bottom"),
        Prop("align", "Popover alignment: start or end", str, "start"),
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def populate(self) -> None:
        """Render popover trigger button and ``[data-popover]`` content section."""
        trigger_label: str = self.props_values.get("trigger_label", "Open")
        content: str = self.props_values.get("content", "")
        position: str = self.props_values.get("position", "bottom")
        align: str = self.props_values.get("align", "start")
        extra: object = self.props_values.get("class_name")

        popover_id = f"sci-pro-popover-{id(self)}"

        classes: list[str] = list(self.default_classes)
        if extra:
            if isinstance(extra, list):
                classes.extend(extra)
            else:
                classes.append(str(extra))

        content_classes = list(_POPOVER_CONTENT)
        # Positional class mappings
        if position == "top":
            content_classes.extend(["bottom-full", "mb-2"])
        elif position == "left":
            content_classes.extend(["right-full", "mr-2"])
        elif position == "right":
            content_classes.extend(["left-full", "ml-2"])
        else:
            content_classes.extend(["top-full", "mt-2"])

        if align == "end":
            content_classes.append("right-0")

        with t.div(class_name=classes, id=popover_id):
            t.button(
                trigger_label,
                type="button",
                aria_expanded="false",
                class_name=_TRIGGER_BASE,
            )

            with t.section(
                data_popover=True,
                aria_hidden="true",
                class_name=content_classes,
            ):
                t(content)

    def on_ready(self) -> None:
        """Re-initialize Basecoat popover JS after PuePy renders."""
        try:
            from src.browser.basecoat_bridge import init_component

            init_component("popover")
        except ImportError:
            pass
