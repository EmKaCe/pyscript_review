"""SciProCard and sub-components — PuePy atomic card layout components.

Provides SciProCard, SciProCardHeader, SciProCardTitle, SciProCardDescription,
SciProCardContent, and SciProCardFooter using Basecoat .card classes.
"""

from puepy import Component, Prop, t


def _merge_prop_classes(
    base: list[str],
    props_values: dict[str, object],
) -> list[str]:
    """Merge default classes with class_name prop supporting str or list."""
    classes: list[str] = list(base)
    extra: object = props_values.get("class_name")
    if extra:
        if isinstance(extra, list):
            classes.extend(extra)  # type: ignore[arg-type]
        else:
            classes.append(str(extra))
    return classes


@t.component()
class SciProCard(Component):
    """Card container with rounded border, padding, and shadow.

    Uses Basecoat ``.card`` class with Tailwind v4 extensions. Child
    elements are slotted directly inside the card body.
    """

    enclosing_tag = "div"
    component_name = "sci-pro-card"

    default_classes = [
        "card",
        "flex",
        "flex-col",
        "gap-6",
        "rounded-xl",
        "border",
        "bg-card",
        "py-6",
        "text-card-foreground",
        "shadow-sm",
    ]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)


@t.component()
class SciProCardHeader(Component):
    """Card header section with optional bottom border."""

    enclosing_tag = "div"
    component_name = "sci-pro-card-header"

    default_classes = ["flex", "flex-col", "gap-1.5", "px-6", "items-start"]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
        Prop("has_border", "Show bottom border separator", bool, False),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)


@t.component()
class SciProCardTitle(Component):
    """Card title with semibold font weight."""

    enclosing_tag = "div"
    component_name = "sci-pro-card-title"

    default_classes = ["leading-none", "font-semibold", "tracking-tight"]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)


@t.component()
class SciProCardDescription(Component):
    """Card description with muted foreground text."""

    enclosing_tag = "div"
    component_name = "sci-pro-card-description"

    default_classes = ["text-sm", "text-muted-foreground"]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)


@t.component()
class SciProCardContent(Component):
    """Card content body with standard padding."""

    enclosing_tag = "div"
    component_name = "sci-pro-card-content"

    default_classes = ["flex", "flex-col", "gap-4", "px-6"]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)


@t.component()
class SciProCardFooter(Component):
    """Card footer section with horizontal layout."""

    enclosing_tag = "div"
    component_name = "sci-pro-card-footer"

    default_classes = ["flex", "items-center", "px-6"]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def get_default_classes(self) -> list[str]:
        return _merge_prop_classes(self.default_classes.copy(), self.props_values)

    def populate(self) -> None:
        pass
