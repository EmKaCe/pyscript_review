"""SciProBadge — PuePy atomic badge/status pill component."""

from puepy import Component, Prop, t


@t.component()
class SciProBadge(Component):
    """Inline-pill badge for statuses, counts, and labels.

    Uses Basecoat ``.badge`` classes with variant and sentiment extensions.
    """

    enclosing_tag = "span"
    component_name = "sci-pro-badge"

    default_classes = [
        "badge",
        "inline-flex",
        "items-center",
        "rounded-full",
        "border",
        "px-2.5",
        "py-0.5",
        "text-xs",
        "font-semibold",
        "transition-colors",
    ]

    VARIANT_CLASSES: dict[str, list[str]] = {
        "default": [
            "border-transparent",
            "bg-primary",
            "text-primary-foreground",
        ],
        "secondary": [
            "border-transparent",
            "bg-secondary",
            "text-secondary-foreground",
        ],
        "destructive": [
            "border-transparent",
            "bg-destructive",
            "text-destructive-foreground",
        ],
        "outline": ["badge-outline", "text-foreground"],
        "positive": [
            "border-transparent",
            "bg-positive-bg",
            "text-positive",
        ],
        "neutral": [
            "border-transparent",
            "bg-neutral-bg",
            "text-neutral",
        ],
        "negative": [
            "border-transparent",
            "bg-negative-bg",
            "text-negative",
        ],
    }

    props = [
        Prop("variant", "Badge variant style", str, "default"),
        Prop("label", "Badge text content", str, ""),
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]

    def populate(self) -> None:
        """Render badge with variant style and label text."""
        variant: str = self.props_values.get("variant", "default")
        label: str = self.props_values.get("label", "")
        extra: str | None = self.props_values.get("class_name")

        classes: list[str] = self.default_classes.copy()
        classes.extend(self.VARIANT_CLASSES.get(variant, self.VARIANT_CLASSES["default"]))
        if extra:
            classes.append(extra)

        with t.span(class_name=classes):
            t(label)
