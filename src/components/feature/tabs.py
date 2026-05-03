"""SciProTabs — Modular tab components matching SvelteKit structure."""

from __future__ import annotations

from puepy import Component, Prop, t


@t.component()
class SciProTabs(Component):
    """Container for a tabbed interface."""

    component_name = "sci-pro-tabs"
    props = [Prop("value", "Active tab value", str, "")]

    def populate(self) -> None:
        with t.div(class_name="w-full", data_tabs_root=""):
            self.insert_slot()


@t.component()
class SciProTabsList(Component):
    """Container for tab triggers."""

    component_name = "sci-pro-tabs-list"

    def populate(self) -> None:
        with t.div(
            class_name="inline-flex h-10 items-center justify-center rounded-md bg-muted p-1 text-muted-foreground w-full mb-4"
        ):
            self.insert_slot()


@t.component()
class SciProTabsTrigger(Component):
    """Button to switch tabs."""

    component_name = "sci-pro-tabs-trigger"
    props = [Prop("value", "Value associated with this tab", str, "")]

    def populate(self) -> None:
        value = self.props_values.get("value")
        active_value = self.parent.parent.props_values.get("value")  # Root Tabs component
        is_active = value == active_value

        classes = [
            "inline-flex items-center justify-center whitespace-nowrap rounded-sm px-3 py-1.5 text-sm font-medium ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 flex-1",
            "bg-background text-foreground shadow-sm" if is_active else "hover:bg-background/50",
        ]

        with t.button(class_name=classes, on_click=lambda _e: self._on_click(value)):
            self.insert_slot()

    def _on_click(self, value: str) -> None:
        # Update the root Tabs value
        root = self.parent.parent
        root.props_values["value"] = value
        root.trigger_event("change", detail={"value": value})
        self.page.redraw_tag(root)


@t.component()
class SciProTabsContent(Component):
    """Panel containing tab content."""

    component_name = "sci-pro-tabs-content"
    props = [Prop("value", "Value associated with this panel", str, "")]

    def populate(self) -> None:
        value = self.props_values.get("value")
        active_value = self.parent.props_values.get("value")  # Root Tabs component

        if value == active_value:
            with t.div(
                class_name="mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            ):
                self.insert_slot()
