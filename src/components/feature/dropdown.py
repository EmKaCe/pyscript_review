"""SciProDropdownMenu — PuePy composite wrapping Basecoat .dropdown-menu JS."""

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
    "justify-between",
    "transition-colors",
    "focus-visible:outline-none",
    "focus-visible:ring-2",
    "focus-visible:ring-ring",
    "focus-visible:ring-offset-2",
]

_MENU_POPOVER = [
    "absolute",
    "z-50",
    "min-w-[8rem]",
    "rounded-md",
    "border",
    "bg-popover",
    "text-popover-foreground",
    "shadow-md",
    "p-1",
    "mt-1",
]


@t.component()
class SciProDropdownMenu(Component):
    """Contextual dropdown menu with trigger button and ``[role=menu]`` items.

    Uses Basecoat JS for open/close, keyboard navigation, and
    ``basecoat:popover`` event coordination. Each item is a dict with:
        - ``label`` (str): Display text.
        - ``action`` (callable | None): Click handler (None for separators/disabled).
        - ``disabled`` (bool): Whether this item is disabled.
        - ``separator`` (bool): Render as a visual separator instead of an item.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-dropdown-menu"

    default_classes = ["dropdown-menu", "relative", "inline-block"]

    props = [
        Prop("trigger_label", "Button label for the dropdown trigger", str, "Menu"),
        Prop("items", "List of dicts with label, action, disabled, separator", list, ()),
        Prop("variant", "Trigger variant: default, outline, ghost", str, "outline"),
        Prop("align", "Menu alignment: start or end", str, "start"),
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def populate(self) -> None:
        """Render dropdown trigger button and ``[role=menu]`` with items."""
        trigger_label: str = self.props_values.get("trigger_label", "Menu")
        items: list[dict] = self.props_values.get("items", [])
        variant: str = self.props_values.get("variant", "outline")
        align: str = self.props_values.get("align", "start")
        extra: object = self.props_values.get("class_name")

        menu_id = f"sci-pro-dropdown-{id(self)}"

        trigger_classes = list(_TRIGGER_BASE)
        if variant == "ghost":
            trigger_classes = [c for c in trigger_classes if c not in ("btn-outline",)]
            trigger_classes.append("btn-ghost")
        elif variant == "default":
            trigger_classes = [c for c in trigger_classes if c not in ("btn-outline",)]
            trigger_classes.append("btn-primary")

        classes: list[str] = list(self.default_classes)
        if extra:
            if isinstance(extra, list):
                classes.extend(extra)
            else:
                classes.append(str(extra))

        popover_classes = list(_MENU_POPOVER)
        if align == "end":
            popover_classes.append("right-0")
        else:
            popover_classes.append("left-0")

        with t.div(class_name=classes, id=menu_id):
            t.button(
                trigger_label,
                type="button",
                aria_expanded="false",
                aria_haspopup="true",
                class_name=trigger_classes,
            )

            with (
                t.div(
                    data_popover=True,
                    aria_hidden="true",
                    class_name=popover_classes,
                ),
                t.div(role="menu"),
            ):
                for i, item in enumerate(items):
                    label: str = item.get("label", "")
                    disabled: bool = item.get("disabled", False)
                    separator: bool = item.get("separator", False)
                    item_id = f"{menu_id}-item-{i}"

                    if separator:
                        t.hr(role="separator", class_name="my-1 border-muted")
                        continue

                    item_attrs: dict[str, object] = {
                        "role": "menuitem",
                        "id": item_id,
                        "class_name": [
                            "flex",
                            "w-full",
                            "cursor-default",
                            "select-none",
                            "items-center",
                            "gap-2",
                            "rounded-sm",
                            "px-2",
                            "py-1.5",
                            "text-sm",
                            "text-popover-foreground",
                            "outline-none",
                            "hover:bg-accent",
                            "hover:text-accent-foreground",
                            "data-[disabled]:pointer-events-none",
                            "data-[disabled]:opacity-50",
                        ],
                    }
                    if disabled:
                        item_attrs["aria_disabled"] = "true"

                    t.button(label, **item_attrs)

    def on_ready(self) -> None:
        """Re-initialize Basecoat dropdown-menu JS after PuePy renders."""
        try:
            from src.browser.basecoat_bridge import init_component

            init_component("dropdown-menu")
        except ImportError:
            pass
