"""SciProTable and sub-components — PuePy atomic table using Basecoat .table classes."""

from puepy import Component, Prop, t


@t.component()
class SciProTable(Component):
    """Table wrapper using Basecoat ``.table`` class with Tailwind extensions."""

    enclosing_tag = "div"
    component_name = "sci-pro-table"

    default_classes = ["w-full", "overflow-auto"]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]

    def populate(self) -> None:
        extra: str | None = self.props_values.get("class_name")
        classes: list[str] = list(self.default_classes)
        if extra:
            classes.append(extra)
        with t.table(class_name=classes):
            self.insert_slot()


@t.component()
class SciProTableHeader(Component):
    """Table header section (``<thead>``)."""

    enclosing_tag = "thead"
    component_name = "sci-pro-table-header"

    default_classes = ["[&_tr]:border-b"]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]


@t.component()
class SciProTableBody(Component):
    """Table body section (``<tbody>``)."""

    enclosing_tag = "tbody"
    component_name = "sci-pro-table-body"

    default_classes = ["[&_tr:last-child]:border-0"]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]


@t.component()
class SciProTableRow(Component):
    """Table row (``<tr>``)."""

    enclosing_tag = "tr"
    component_name = "sci-pro-table-row"

    default_classes = [
        "border-b",
        "transition-colors",
        "hover:bg-muted/50",
        "data-[state=selected]:bg-muted",
    ]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]


@t.component()
class SciProTableHead(Component):
    """Table header cell (``<th>``)."""

    enclosing_tag = "th"
    component_name = "sci-pro-table-head"

    default_classes = [
        "h-12",
        "px-4",
        "text-left",
        "align-middle",
        "font-medium",
        "text-muted-foreground",
        "[&:has([role=checkbox])]:pr-0",
    ]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]


@t.component()
class SciProTableCell(Component):
    """Table data cell (``<td>``)."""

    enclosing_tag = "td"
    component_name = "sci-pro-table-cell"

    default_classes = [
        "p-4",
        "align-middle",
        "[&:has([role=checkbox])]:pr-0",
    ]

    props = [
        Prop("class_name", "Additional Tailwind classes", str, None),
    ]

    def populate(self) -> None:
        extra: str | None = self.props_values.get("class_name")
        classes: list[str] = list(self.default_classes)
        if extra:
            classes.append(extra)
        with t.td(class_name=classes):
            self.insert_slot()
