"""Basecoat JS bridge for SciPro Review App.

Re-initializes Basecoat JavaScript components after PuePy redraws.
PuePy uses morphdom to patch the DOM, which can destroy Basecoat's
JS event listeners and internal state. This module provides functions
to re-trigger Basecoat initialization for newly rendered elements.

WHEN TO CALL:
  - After PuePy page transitions that render Basecoat JS components
    (e.g., in Page.on_ready() or after navigation)
  - After dynamic DOM insertion of Basecoat elements
    (e.g., programmatically adding a tab panel or dropdown)
  - Do NOT call on every redraw — only after page transitions or
    targeted component creation
"""

# Basecoat JS component names that can be initialized individually.
SUPPORTED_COMPONENTS = frozenset(
    {
        "tabs",
        "select",
        "dropdown-menu",
        "popover",
        "toast",
        "sidebar",
    }
)


def init_basecoat() -> None:
    """Re-initialize ALL Basecoat JS components.

    Calls ``window.basecoat.initAll()`` which clears initialization
    flags for every registered component and re-runs their init
    functions across the entire document. Use after PuePy page
    transitions that render multiple Basecoat components at once.

    No-op when running outside a browser (pytest, SSR).
    """
    try:
        from js import window  # type: ignore[import-untyped]

        if hasattr(window, "basecoat"):
            window.basecoat.initAll()
    except ImportError:
        pass


def init_component(name: str) -> None:
    """Re-initialize a single Basecoat JS component type.

    Calls ``window.basecoat.init(name)`` which clears the initialization
    flag for the named component and re-runs its init function on all
    matching elements. Use for targeted re-init after inserting a
    specific component into the DOM.

    Args:
        name: Basecoat component name. Must be one of:
            ``tabs``, ``select``, ``dropdown-menu``,
            ``popover``, ``toast``, ``sidebar``.

    Raises:
        ValueError: If name is not a recognized Basecoat component.

    No-op when running outside a browser (pytest, SSR).
    """
    if name not in SUPPORTED_COMPONENTS:
        raise ValueError(
            f"Unknown Basecoat component '{name}'. "
            f"Must be one of: {', '.join(sorted(SUPPORTED_COMPONENTS))}."
        )

    try:
        from js import window  # type: ignore[import-untyped]

        if hasattr(window, "basecoat"):
            window.basecoat.init(name)
    except ImportError:
        pass
