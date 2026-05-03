"""SciProSkeleton — PuePy atomic loading placeholder component."""

from puepy import Component, Prop, t


@t.component()
class SciProSkeleton(Component):
    """Loading placeholder with shape variants and animated pulse.

    Uses Basecoat ``.skeleton`` class with Tailwind v4 extensions.
    """

    component_name = "sci-pro-skeleton"

    _SKELETON_BASE = [
        "skeleton",
        "animate-pulse",
        "rounded-md",
        "bg-muted",
    ]

    _VARIANT_CLASSES: dict[str, list[str]] = {
        "text": ["h-4", "w-full"],
        "circle": ["h-12", "w-12", "rounded-full"],
        "rectangle": ["h-32", "w-full", "rounded-lg"],
    }

    props = [
        Prop("variant", "Skeleton shape: text, circle, rectangle", str, "text"),
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]

    def populate(self) -> None:
        """Render a pulsing skeleton placeholder."""
        variant: str = self.props_values.get("variant", "text")
        extra: str | None = self.props_values.get("class_name")

        classes: list[str] = self._SKELETON_BASE.copy()
        classes.extend(self._VARIANT_CLASSES.get(variant, self._VARIANT_CLASSES["text"]))
        if extra:
            classes.append(extra)

        with t.div(class_name=classes, aria_hidden="true"):
            pass
