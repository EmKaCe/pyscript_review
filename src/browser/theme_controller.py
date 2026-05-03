"""Theme controller for SciPro Review App.

Provides module-level functions for toggling light/dark/system theme modes.
Toggles the ``.dark`` class on ``<html>`` and persists choice to localStorage.

Functions:
    toggle_theme: Cycle theme: light -> dark -> system -> light.
    get_theme: Return the current theme mode ("light", "dark", "system").
    set_theme: Set and apply a specific theme mode.
    apply_theme: Apply the current theme to the DOM.
    initialize: Load saved theme and apply. Call at app boot.
"""

_STORAGE_KEY = "scipro-theme"
_VALID_MODES: tuple[str, str, str] = ("light", "dark", "system")

# In-memory fallback when running outside a browser (pytest, SSR).
_memory_store: dict[str, str] = {}


def _get_js_window():
    """Import and return the ``js.window`` module, or None if unavailable.

    Returns:
        The JS window object, or None if not in a browser environment.
    """
    try:
        from js import window  # type: ignore[import-untyped]

        return window
    except ImportError:
        return None


def _get_local_storage(window):
    """Safely access localStorage, returning None if unavailable."""
    try:
        return window.localStorage
    except Exception:  # noqa: BLE001
        return None


def get_system_theme() -> str:
    """Detect OS-level color scheme preference.

    Returns:
        "dark" if the OS prefers dark mode, "light" otherwise.
    """
    window = _get_js_window()
    if window is not None:
        try:
            media_query = window.matchMedia("(prefers-color-scheme: dark)")
            return "dark" if media_query.matches else "light"
        except Exception:  # noqa: BLE001
            pass
    return "light"


def _load_saved_theme() -> str | None:
    """Load saved theme preference from localStorage.

    Returns:
        Theme mode string ("light", "dark", "system") or None if not set.
    """
    window = _get_js_window()
    if window is not None:
        storage = _get_local_storage(window)
        if storage is not None:
            try:
                value = storage.getItem(_STORAGE_KEY)
                if value in _VALID_MODES:
                    return value
            except Exception:  # noqa: BLE001
                pass
    # Fallback to in-memory store.
    saved = _memory_store.get(_STORAGE_KEY)
    if saved in _VALID_MODES:
        return saved
    return None


def _save_theme(mode: str) -> None:
    """Persist theme choice to localStorage.

    Args:
        mode: One of "light", "dark", "system".

    Raises:
        ValueError: If mode is not a valid theme.
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"Invalid theme mode: {mode}. Must be one of {_VALID_MODES}.")

    window = _get_js_window()
    if window is not None:
        storage = _get_local_storage(window)
        if storage is not None:
            try:
                storage.setItem(_STORAGE_KEY, mode)
                return
            except Exception:  # noqa: BLE001
                pass
    # Fallback: store in memory.
    _memory_store[_STORAGE_KEY] = mode


def apply_theme(mode: str) -> None:
    """Apply theme by toggling ``.dark`` class on ``<html>`` element.

    For "system" mode, resolves to the current OS preference before applying.

    Args:
        mode: "light", "dark", or "system".

    Raises:
        ValueError: If mode is not a valid theme.
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"Invalid theme mode: {mode}. Must be one of {_VALID_MODES}.")

    effective = get_system_theme() if mode == "system" else mode

    try:
        from js import document  # type: ignore[import-untyped]

        html = document.documentElement
        if effective == "dark":
            html.classList.add("dark")
        else:
            html.classList.remove("dark")
    except ImportError:
        pass  # No-op outside browser.


def get_theme() -> str:
    """Return the current theme mode.

    Checks localStorage first, then falls back to in-memory store,
    and finally defaults to "system".

    Returns:
        One of "light", "dark", "system".
    """
    saved = _load_saved_theme()
    if saved is not None:
        return saved
    return "system"


def set_theme(mode: str) -> None:
    """Set and apply a specific theme mode.

    Args:
        mode: "light", "dark", or "system".

    Raises:
        ValueError: If mode is not a valid theme.
    """
    if mode not in _VALID_MODES:
        raise ValueError(f"Invalid theme mode: {mode}. Must be one of {_VALID_MODES}.")
    _save_theme(mode)
    apply_theme(mode)


def toggle_theme() -> str:
    """Cycle the theme: light -> dark -> system -> light.

    Returns:
        The new theme mode after toggling.
    """
    current = get_theme()
    next_index = (_VALID_MODES.index(current) + 1) % len(_VALID_MODES)
    next_theme = _VALID_MODES[next_index]
    set_theme(next_theme)
    return next_theme


def initialize() -> None:
    """Load saved theme and apply it. Call at app boot."""
    saved = _load_saved_theme()
    if saved is not None:
        apply_theme(saved)
    else:
        apply_theme("system")
