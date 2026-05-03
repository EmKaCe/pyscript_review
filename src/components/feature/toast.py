"""SciProToast — PuePy toast notification service wrapping Basecoat toast JS."""

from puepy import Component, Prop, t


def show_toast(
    title: str = "",
    description: str = "",
    variant: str = "info",
    duration: int = 3000,
) -> None:
    """Dispatch a Basecoat toast notification via ``basecoat:toast`` custom event.

    Creates a toast that appears in the ``#toaster`` container managed
    by the ``SciProToaster`` component. Safe to call in pytest (no JS).

    Args:
        title: Toast heading text.
        description: Toast body text.
        variant: Visual category — ``"info"``, ``"success"``, ``"error"``, ``"warning"``.
        duration: Auto-dismiss timeout in ms (-1 for persistent).
    """
    try:
        from js import CustomEvent, document
        from pyodide.ffi import to_js

        config = {
            "title": title,
            "description": description,
            "category": variant,
            "duration": duration,
        }
        detail_data = to_js({"config": config})
        event = CustomEvent.new("basecoat:toast", to_js({"detail": detail_data}))
        document.dispatchEvent(event)
    except ImportError:
        pass


@t.component()
class SciProToaster(Component):
    """Renders the ``#toaster`` container for Basecoat toast notifications.

    This component creates the global toast host element. Place it once
    in your root page layout — all ``show_toast()`` calls will render
    into this container.

    Initializes Basecoat toast JS in ``on_ready()`` so new toasts are
    managed correctly after PuePy renders.
    """

    enclosing_tag = "section"
    component_name = "sci-pro-toaster"

    default_classes = [
        "fixed",
        "bottom-4",
        "right-4",
        "z-50",
        "flex",
        "flex-col",
        "gap-2",
        "max-w-sm",
        "w-full",
        "pointer-events-none",
        "[&>_.toast]:pointer-events-auto",
    ]

    props = [
        Prop("class_name", "Extra Tailwind classes", object, None),
    ]

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Set element_id to 'toaster' for Basecoat JS selector targeting."""
        super().__init__(*args, **kwargs)
        self.element_id = "toaster"

    def populate(self) -> None:
        """Toaster is a container — children (toasts) are inserted by JS."""
        pass

    def on_ready(self) -> None:
        """Re-initialize Basecoat toast JS after PuePy renders the #toaster."""
        try:
            from src.browser.basecoat_bridge import init_component

            init_component("toast")
        except ImportError:
            pass
