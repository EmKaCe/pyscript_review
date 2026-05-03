"""SciProIcon — PuePy atomic icon component using inline SVG or CSS class rendering."""

from puepy import Component, Prop, t

_SIZE_MAP: dict[str, list[str]] = {
    "xs": ["h-3", "w-3"],
    "sm": ["h-4", "w-4"],
    "md": ["h-5", "w-5"],
    "lg": ["h-6", "w-6"],
    "xl": ["h-8", "w-8"],
}


@t.component()
class SciProIcon(Component):
    """Inline SVG icon rendered via CSS background-image and jsdelivr.

    Icons are rendered using a ``<span>`` with a CSS background-image
    pointing to a lucide-static SVG on jsdelivr, keeping the DOM extremely clean.
    """

    enclosing_tag = "span"
    component_name = "sci-pro-icon"

    default_classes = ["inline-block", "shrink-0"]

    props = [
        Prop("name", "Icon name (e.g. check, x, search)", str, "circle"),
        Prop("size", "Size variant (xs, sm, md, lg, xl)", str, "md"),
        Prop("class_name", "Additional Tailwind classes", str, None),
        Prop("aria_hidden", "Hide from screen readers", bool, True),
        Prop("aria_label", "Accessible label text", str, None),
    ]

    def populate(self) -> None:
        """Render icon span with CSS background-image."""
        name: str = self.props_values.get("name", "circle")
        size: str = self.props_values.get("size", "md")
        extra_class: str | None = self.props_values.get("class_name")
        aria_hidden: bool = self.props_values.get("aria_hidden", True)
        aria_label: str | None = self.props_values.get("aria_label")

        classes: list[str] = list(self.default_classes)
        size_classes = _SIZE_MAP.get(size, _SIZE_MAP["md"])
        classes.extend(size_classes)
        if extra_class:
            classes.append(extra_class)
        self.class_name = " ".join(classes)

        # Map Tailwind size classes to rem for explicit sizing
        rem_size = "1.25rem"  # Default md (h-5)
        if "h-3" in size_classes:
            rem_size = "0.75rem"
        elif "h-4" in size_classes:
            rem_size = "1rem"
        elif "h-6" in size_classes:
            rem_size = "1.5rem"
        elif "h-8" in size_classes:
            rem_size = "2rem"

        url = f"https://cdn.jsdelivr.net/npm/lucide-static@0.447.0/icons/{name}.svg"
        self.attrs["style"] = (
            f"-webkit-mask-image: url('{url}'); "
            f"mask-image: url('{url}'); "
            f"-webkit-mask-size: contain; "
            f"mask-size: contain; "
            f"-webkit-mask-repeat: no-repeat; "
            f"mask-repeat: no-repeat; "
            f"-webkit-mask-position: center; "
            f"mask-position: center; "
            f"background-color: currentColor; "
            f"width: {rem_size}; "
            f"height: {rem_size}; "
            f"display: inline-block;"
        )

        if aria_hidden:
            self.attrs["aria-hidden"] = "true"
        elif aria_label:
            self.attrs["aria-label"] = aria_label
            self.attrs["role"] = "img"
