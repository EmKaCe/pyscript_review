"""SciProCriteriaList — Feature component iterating over rubric categories."""

from puepy import Component, t

from src.state import ReviewState


@t.component()
class SciProCriteriaList(Component):
    """Iterates over rubric categories and renders a card for each."""

    component_name = "sci-pro-criteria-list"
    redraw_on_app_state_changes = ["criteria_bundle", "category_selections"]

    def populate(self) -> None:
        """Render the list of categories."""
        bundle = self.application.state.get("criteria_bundle")
        if not bundle:
            with t.div(class_name="rounded-md border border-dashed p-8 text-center"):
                t.p("Select an assignment to view criteria", class_name="text-sm text-muted-foreground")
            return

        rs = ReviewState(self.application.state)

        with t.div(class_name="flex flex-col gap-4"):
            for cat in bundle.categories:
                with t.sci_pro_card(id=f"category-{cat.slug}"):
                    with t.sci_pro_card_header(class_name="pb-3"):
                        t.sci_pro_card_title(cat.name, class_name="text-base")
                    with t.sci_pro_card_content():
                        t.sci_pro_category_panel(
                            category=cat,
                            category_key=cat.slug,
                            selections=rs.category_selections.get(cat.slug)
                        )
