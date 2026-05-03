"""Base page with app shell layout: sidebar, header, and main content area.

All page-level components extend this class. Subclasses override
``populate_content()`` instead of ``populate()``.

Layout matches the svelte_review design:
- Desktop (≥1024px): Fixed sidebar (w-64, bg-sidebar) + header + main content.
- Mobile (<1024px): Mobile header with hamburger → Sheet overlay sidebar.
"""

from puepy import Component, Page, t  # noqa: F401
from puepy.runtime import window

from src.browser.basecoat_bridge import init_basecoat
from src.browser.theme_controller import toggle_theme

_LOGO_ICON_NAME = "scroll"


class BasePage(Page):
    """Shared page shell: sidebar navigation, header bar, and content slot.

    Subclasses MUST override ``populate_content()`` to render
    page-specific content into the app shell.
    """

    redraw_on_app_state_changes = [
        "mode",
        "theme",
        "sidebar_open",
        "assignment_id",
        "criteria_bundle",
    ]

    def populate(self) -> None:
        """Render the full app shell: sidebar, header, main content."""
        self._route = self._get_current_route()

        # Sync app state mode with route
        if self._route == "/":
            self.application.state["active_page"] = "home"
        elif self._route == "/review":
            self.application.state["active_page"] = "review"
        elif self._route == "/settings":
            self.application.state["active_page"] = "settings"
        elif self._route == "/docs":
            self.application.state["active_page"] = "docs"

        with t.div(
            class_name="flex h-screen w-screen overflow-hidden bg-background text-foreground font-sans"
        ):
            self._render_desktop_sidebar()

            with t.div(class_name="flex flex-col flex-1 overflow-hidden"):
                self._render_mobile_header()

                with t.div(class_name="flex-1 overflow-y-auto bg-background"):
                    with t.div(class_name="px-4 py-6 md:px-8 md:py-8 lg:px-12"):
                        self.populate_content()

    def _render_desktop_sidebar(self) -> None:
        """Render the fixed sidebar for desktop layout (≥1024px)."""
        with t.aside(
            class_name="hidden lg:flex lg:flex-col w-64 shrink-0 border-r border-sidebar-border bg-sidebar text-sidebar-foreground"
        ):
            with t.div(
                class_name="flex items-center gap-2 px-4 py-5 border-b border-sidebar-border"
            ):
                t.sci_pro_icon(name=_LOGO_ICON_NAME, size="md", class_name="text-sidebar-primary")
                with t.span(class_name="text-lg font-bold tracking-tight"):
                    t("SciPro")

            with t.nav(class_name="flex-1 p-3 flex flex-col gap-1 overflow-y-auto"):
                self._render_sidebar_nav_items()
                self._render_criteria_section()

    def _render_sidebar_nav_items(self) -> None:
        """Render sidebar navigation links with button-style styling."""
        for icon_name, label, href in self._nav_items():
            # Check if current route starts with href (to handle hash routing)
            route = self._route
            if not route.startswith("/"):
                route = "/" + route

            clean_href = href.replace("#", "")
            if not clean_href.startswith("/"):
                clean_href = "/" + clean_href

            is_active = route == clean_href
            active_cls = " bg-secondary text-secondary-foreground" if is_active else ""
            hover_cls = "" if is_active else " hover:bg-accent hover:text-accent-foreground"
            with t.a(
                href=href,
                class_name=f"flex items-center gap-2 w-full px-3 py-2 rounded-md text-sm font-medium justify-start transition-colors{active_cls}{hover_cls}",
            ):
                t.sci_pro_icon(name=icon_name, size="sm")
                t.span(label)

    def _render_criteria_section(self) -> None:
        """Render criteria navigation when on the review page."""
        if self._route != "/review":
            return

        assignment_id = self.application.state.get("assignment_id", "")
        if not assignment_id:
            return

        criteria_bundle = self.application.state.get("criteria_bundle")
        if criteria_bundle is None:
            return

        categories = getattr(criteria_bundle, "categories", [])
        if not categories:
            return

        with t.p(
            class_name="mt-4 mb-1 px-2 text-xs font-semibold uppercase tracking-wider text-sidebar-foreground/40"
        ):
            t("Criteria")

        for cat in categories:
            slug = getattr(cat, "slug", "")
            name = getattr(cat, "name", str(cat))
            with t.a(
                href=f"#category-{slug}",
                class_name="flex items-center gap-2 w-full px-3 py-1.5 rounded-md text-sm text-sidebar-foreground/70 hover:text-sidebar-foreground transition-colors",
                on_click=self._on_criteria_click,
                data_slug=slug,
            ):
                t.span("›", class_name="text-sidebar-foreground/50")
                with t.span(class_name="truncate"):
                    t(name)

    def _on_criteria_click(self, event=None) -> None:
        """Scroll to the clicked criteria category in the main content."""
        if event is None or window is None:
            return

        try:
            from js import document  # type: ignore[import-untyped]

            # Find the anchor element even if a child was clicked
            el = event.target
            for _ in range(5):
                if el is None:
                    break
                if getattr(el, "tagName", "") == "A":
                    break
                el = getattr(el, "parentElement", None)

            if el:
                slug = el.getAttribute("data-slug")
                if slug:
                    target_id = f"category-{slug}"
                    target = document.getElementById(target_id)
                    if target:
                        target.scrollIntoView({"behavior": "smooth", "block": "start"})
                        # Prevent default hash jump
                        event.preventDefault()
        except Exception:
            pass

    def _render_mobile_header(self) -> None:
        """Render mobile-only header with hamburger and brand."""
        with t.header(class_name="flex items-center border-b px-4 py-3 lg:hidden"):
            t.sci_pro_button(
                variant="ghost",
                icon="menu",
                on_click=self._on_hamburger_click,
                icon_size="sm",
                class_name="size-9",
            )
            with t.span(class_name="ml-2 text-lg font-bold tracking-tight"):
                t("SciPro")

        if self.application.state.get("sidebar_open") is True:
            self._render_mobile_sidebar_overlay()

    def _render_mobile_sidebar_overlay(self) -> None:
        """Render mobile sidebar as an overlay sheet from the left."""
        with t.div(
            class_name="fixed inset-0 z-40 lg:hidden",
            on_click=self._on_overlay_click,
        ):
            with t.div(
                class_name="fixed top-0 left-0 h-screen w-64 bg-sidebar text-sidebar-foreground border-r border-sidebar-border shadow-lg transition-transform duration-300 ease-in-out z-50",
                on_click=self._on_sidebar_content_click,
            ):
                with t.div(
                    class_name="flex items-center gap-2 px-4 py-5 border-b border-sidebar-border"
                ):
                    t.sci_pro_icon(
                        name=_LOGO_ICON_NAME, size="md", class_name="text-sidebar-primary"
                    )
                    with t.span(class_name="text-lg font-bold tracking-tight"):
                        t("SciPro")

                with t.nav(class_name="flex-1 p-3 flex flex-col gap-1 overflow-y-auto"):
                    self._render_sidebar_nav_items()

    def _on_overlay_click(self, _event=None) -> None:
        """Close mobile sidebar when backdrop overlay is clicked."""
        self.application.state["sidebar_open"] = False

    def _on_sidebar_content_click(self, event=None) -> None:
        """Close mobile sidebar when a nav link inside is clicked."""
        try:
            target = getattr(event, "target", None)
            for _ in range(5):
                if target is None:
                    return
                if getattr(target, "tagName", "") == "A":
                    self.application.state["sidebar_open"] = False
                    return
                target = getattr(target, "parentElement", None)
        except Exception:  # noqa: BLE001
            pass

    def _on_hamburger_click(self, _event=None) -> None:
        """Toggle the mobile sidebar sheet."""
        current = self.application.state.get("sidebar_open", False)
        self.application.state["sidebar_open"] = not current

    def on_ready(self) -> None:
        """Re-initialize Basecoat JS components after PuePy page transition.

        Called when the page is mounted into the DOM.  Ensures dropdowns,
        tabs, modals and other Basecoat JS widgets receive their init
        calls after morphdom patches the DOM.
        """
        init_basecoat()

    def _on_theme_toggle(self, _event=None) -> None:
        """Handle theme toggle button click: cycles light→dark→system."""
        new_theme = toggle_theme()
        self.application.state["theme"] = new_theme

    def populate_content(self) -> None:
        """Override in subclasses to render page-specific content."""
        raise NotImplementedError(
            "Subclasses must override populate_content() to render page content"
        )

    def _get_current_route(self) -> str:
        """Extract the current route from the window location hash."""
        if window is None:
            return "/"
        hash_val = getattr(window.location, "hash", "")
        if hash_val.startswith("#"):
            return hash_val[1:] or "/"
        return "/"

    @staticmethod
    def _nav_items() -> list[tuple[str, str, str]]:
        """Return navigation items as (icon_name, label, href) tuples.

        Href values use the ``#/`` prefix required by PuePy's
        ``LINK_MODE_HASH`` router so that ``<a>`` clicks trigger
        client-side navigation instead of a full page load.
        """
        return [
            ("house", "Home", "#/"),
            ("file-text", "Review", "#/review"),
            ("sliders-horizontal", "Settings", "#/settings"),
            ("book-open", "Docs", "docs-static/index.html"),
        ]
