"""SciProButton — PuePy atomic button component with Basecoat CSS variants."""

from puepy import Component, Prop, t


@t.component()
class SciProButton(Component):
    """Button component with variant styles and optional icon.

    Supports the Basecoat ``.btn`` CSS classes plus Tailwind v4 extensions
    via CSS custom properties (``bg-primary``, ``text-primary-foreground``, etc.).
    """

    enclosing_tag = "button"
    component_name = "sci-pro-button"

    default_classes = [
        "btn",
        "inline-flex",
        "items-center",
        "justify-center",
        "gap-2",
        "h-10",
        "px-4",
        "py-2",
        "text-sm",
        "font-medium",
        "whitespace-nowrap",
        "transition-colors",
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-ring",
        "focus-visible:ring-offset-2",
        "disabled:pointer-events-none",
        "disabled:opacity-50",
        "[&_svg]:pointer-events-none",
        "[&_svg]:shrink-0",
    ]

    VARIANT_CLASSES: dict[str, list[str]] = {
        "primary": [
            "btn-primary",
            "bg-primary",
            "text-primary-foreground",
            "hover:bg-primary/90",
        ],
        "secondary": [
            "btn-secondary",
            "bg-secondary",
            "text-secondary-foreground",
            "hover:bg-secondary/80",
        ],
        "destructive": [
            "btn-destructive",
            "bg-destructive",
            "text-destructive-foreground",
            "hover:bg-destructive/90",
        ],
        "ghost": [
            "btn-ghost",
            "hover:bg-accent",
            "hover:text-accent-foreground",
        ],
        "outline": [
            "btn-outline",
            "border",
            "border-input",
            "bg-background",
            "hover:bg-accent",
            "hover:text-accent-foreground",
        ],
        "link": [
            "btn-link",
            "text-primary",
            "underline-offset-4",
            "hover:underline",
        ],
    }

    props = [
        Prop("variant", "Button variant", str, "primary"),
        Prop("label", "Button text", str, ""),
        Prop("icon", "Optional icon name", str, None),
        Prop("disabled", "Disabled state", bool, False),
        Prop("class_name", "Additional Tailwind classes", str, None),
        Prop("on_click", "Click handler", object, None),
        Prop("icon_size", "Icon size class suffix", str, "sm"),
    ]

    def populate(self) -> None:
        """Render button with optional icon and label."""
        variant = self.props_values.get("variant", "primary")
        label = self.props_values.get("label", "")
        icon = self.props_values.get("icon")
        disabled = self.props_values.get("disabled", False)
        on_click = self.props_values.get("on_click")
        extra = self.props_values.get("class_name")
        icon_size = self.props_values.get("icon_size", "sm")

        classes: list[str] = self.default_classes.copy()
        classes.extend(self.VARIANT_CLASSES.get(variant, self.VARIANT_CLASSES["primary"]))
        if extra:
            classes.append(extra)

        self.class_name = " ".join(classes)

        if disabled:
            self.attrs["disabled"] = ""
        else:
            self.attrs.pop("disabled", None)

        if on_click is not None:
            self.on("click", on_click)

        if icon:
            t.sci_pro_icon(name=icon, size=icon_size)
        if label:
            t.span(label, class_name="leading-none")
