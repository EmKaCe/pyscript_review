"""SciProSidebarSheet — PuePy composite sidebar + mobile sheet wrapping Basecoat JS."""

from puepy import Component, Prop, t

_SIDEBAR_CLASSES = [
    "sidebar",
    "fixed",
    "top-0",
    "left-0",
    "z-40",
    "h-screen",
    "w-64",
    "border-r",
    "bg-background",
    "transition-transform",
    "duration-300",
    "ease-in-out",
]

_SIDEBAR_COLLAPSED = [
    "-translate-x-full",
    "md:translate-x-0",
]

_OVERLAY_CLASSES = [
    "fixed",
    "inset-0",
    "z-30",
    "bg-black/50",
    "md:hidden",
]

_NAV_ITEM_BASE = [
    "flex",
    "items-center",
    "gap-3",
    "rounded-md",
    "px-3",
    "py-2",
    "text-sm",
    "font-medium",
    "text-muted-foreground",
    "transition-colors",
    "hover:bg-accent",
    "hover:text-accent-foreground",
]

_NAV_ITEM_ACTIVE = [
    "bg-accent",
    "text-accent-foreground",
]


@t.component()
class SciProSidebarSheet(Component):
    """Collapsible sidebar navigation with mobile sheet/drawer overlay.

    Desktop (≥768px): fixed sidebar with collapsible nav items.
    Mobile (<768px): slide-in sheet with backdrop overlay.

    Each nav item is a dict with:
        - ``label`` (str): Display text.
        - ``href`` (str): Navigation target.
        - ``icon`` (str | None): Optional icon name.
        - ``active`` (bool): Current page highlight.
        - ``children`` (list[dict] | None): Nested sub-items.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-sidebar-sheet"

    props = [
        Prop("items", "List of nav dicts with label, href, icon, active", list, ()),
        Prop("open", "Open state for mobile sheet", bool, False),
        Prop("variant", "Sidebar variant: default or compact", str, "default"),
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def default_initial_state(self) -> dict:
        """Local UI state: whether mobile sheet is open."""
        return {"is_open": False}

    def populate(self) -> None:
        """Render sidebar with nav items and mobile overlay."""
        items: list[dict] = self.props_values.get("items", [])
        variant: str = self.props_values.get("variant", "default")
        extra: object = self.props_values.get("class_name")
        is_open: bool = bool(self.state.get("is_open", False))

        sidebar_id = f"sci-pro-sidebar-{id(self)}"

        # Sidebar classes
        sidebar_classes = list(_SIDEBAR_CLASSES)
        if variant == "compact":
            sidebar_classes.extend(["w-16", "md:w-16"])
        else:
            sidebar_classes.extend(["w-64", "md:w-64"])

        if extra:
            if isinstance(extra, list):
                sidebar_classes.extend(extra)
            else:
                sidebar_classes.append(str(extra))

        sidebar_classes.extend(_SIDEBAR_COLLAPSED)

        # Mobile overlay
        if is_open:
            with t.div(
                class_name=_OVERLAY_CLASSES,
                on_click=self._on_overlay_click,
            ):
                pass

        # Sidebar element
        with (
            t.div(
                id=sidebar_id,
                class_name=sidebar_classes,
                data_initial_open="false",
                data_initial_mobile_open=str(is_open).lower(),
                data_breakpoint="768",
                aria_hidden=str(not is_open).lower(),
            ),
            t.aside(
                class_name="flex flex-col h-full pt-16 px-3",
            ),
            t.nav(class_name="flex flex-col gap-1"),
        ):
            for i, item in enumerate(items):
                self._render_nav_item(item, sidebar_id, i)

    def _render_nav_item(self, item: dict, parent_id: str, idx: int) -> None:
        """Render a single nav item, optionally with children."""
        label: str = item.get("label", f"Item {idx + 1}")
        href: str = item.get("href", "#")
        icon: str | None = item.get("icon")
        active: bool = item.get("active", False)
        children: list[dict] | None = item.get("children")

        item_id = f"{parent_id}-item-{idx}"

        item_classes = list(_NAV_ITEM_BASE)
        if active:
            item_classes.extend(_NAV_ITEM_ACTIVE)

        link_attrs: dict[str, object] = {
            "href": href,
            "class_name": item_classes,
        }
        if active:
            link_attrs["aria_current"] = "page"

        if children:
            # Render as collapsible group header
            with t.div(class_name="flex flex-col gap-0.5"):
                with t.a(**link_attrs):
                    if icon:
                        t.sci_pro_icon(name=icon, size="sm")
                    t.span(label, class_name="flex-1")

                for ci, child in enumerate(children):
                    child_label: str = child.get("label", f"Sub {ci + 1}")
                    child_href: str = child.get("href", "#")
                with t.a(**link_attrs):
                    if icon:
                        t.sci_pro_icon(name=icon, size="sm")
                    t.span(label, class_name="flex-1")

                for ci, child in enumerate(children):
                    child_label: str = child.get("label", f"Sub {ci + 1}")
                    child_href: str = child.get("href", "#")

                for ci, child in enumerate(children):
                    child_label: str = child.get("label", f"Sub {ci + 1}")
                    child_href: str = child.get("href", "#")
                    child_active: bool = child.get("active", False)
                    child_id = f"{item_id}-child-{ci}"

                    child_classes = list(_NAV_ITEM_BASE)
                    child_classes.append("pl-9")
                    if child_active:
                        child_classes.extend(_NAV_ITEM_ACTIVE)

                    child_attrs: dict[str, object] = {
                        "href": child_href,
                        "id": child_id,
                        "class_name": child_classes,
                    }
                    if child_active:
                        child_attrs["aria_current"] = "page"

                    t.a(child_label, **child_attrs)
        else:
            with t.a(**link_attrs):
                if icon:
                    t.sci_pro_icon(name=icon, size="sm")
                t.span(label)

    def _on_overlay_click(self, _event: object) -> None:
        """Close mobile sheet when backdrop overlay is clicked."""
        self.state["is_open"] = False
        self.page.redraw_tag(self)

    def on_ready(self) -> None:
        """Re-initialize Basecoat sidebar JS after PuePy renders."""
        try:
            from src.browser.basecoat_bridge import init_component

            init_component("sidebar")
        except ImportError:
            pass
