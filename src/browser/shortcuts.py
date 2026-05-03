"""Keyboard shortcuts system for SciPro Review App.

Provides ``register_shortcut``, ``unregister_shortcut``, and
``register_default_shortcuts`` for global keydown handling.

All handlers use ``create_proxy`` and call ``event.preventDefault()``.
In non-Pyodide environments (pytest) all operations are safe no-ops.
"""

from collections.abc import Callable

_SHORTCUTS: dict[str, dict] = {
    "save_session": {
        "keys": ["ctrl", "s"],
        "description": "Save session to localStorage",
        "category": "Actions",
    },
    "undo": {
        "keys": ["ctrl", "z"],
        "description": "Undo last change",
        "category": "General",
    },
    "redo_shift_z": {
        "keys": ["ctrl", "shift", "z"],
        "description": "Redo last undone change",
        "category": "General",
    },
    "redo_y": {
        "keys": ["ctrl", "y"],
        "description": "Redo last undone change",
        "category": "General",
    },
    "mode_toggle": {
        "keys": ["alt", "shift", "g"],
        "description": "Toggle Student/Grader mode",
        "category": "General",
    },
    "escape": {
        "keys": ["escape"],
        "description": "Close modal or cancel",
        "category": "General",
    },
}

_DEFAULT_KEYS: list[str] = [
    "ctrl+s",
    "ctrl+z",
    "ctrl+shift+z",
    "ctrl+y",
    "alt+shift+g",
    "escape",
]

# Track registered proxies so they can be cleaned up.
# Maps: key_string -> {"handler": Callable, "proxy": Proxy}
_registered: dict[str, dict] = {}

# Lazy-loaded references (set on first use of register_shortcut).
_window = None
_create_proxy = None


def _ensure_js() -> bool:
    """Import JS interop references; return False if unavailable."""
    global _window, _create_proxy  # noqa: PLW0603
    if _window is not None:
        return True
    try:
        from puepy.runtime import window
        from pyodide.ffi import create_proxy  # noqa: F811

        _window = window
        _create_proxy = create_proxy
        return True
    except ImportError:
        return False


def _parse_key(key: str) -> tuple[set[str], str]:
    """Parse a shortcut key string into (modifiers_set, main_key).

    Args:
        key: Shortcut string like ``"ctrl+s"`` or ``"alt+shift+g"``.

    Returns:
        Tuple of (set of modifier names, main key name).
    """
    parts = key.lower().split("+")
    modifiers = {"ctrl", "alt", "shift"} & set(parts)
    main = [p for p in parts if p not in modifiers][0] if parts else parts[0]
    return modifiers, main


def _make_handler(
    key: str,
    callback: Callable[[], None],
) -> Callable | None:
    """Build a keydown handler that matches *key* and calls *callback*.

    Returns a callable suitable for ``window.addEventListener``, or
    ``None`` if JS interop is unavailable.
    """
    target_modifiers, target_key = _parse_key(key)

    def on_keydown(event) -> None:
        modifiers: set[str] = set()
        if event.ctrlKey:
            modifiers.add("ctrl")
        if event.altKey:
            modifiers.add("alt")
        if event.shiftKey:
            modifiers.add("shift")

        key_pressed = str(event.key).lower()

        if key_pressed in {"control", "alt", "shift", "meta"}:
            return
        if key_pressed != target_key:
            return
        if modifiers != target_modifiers:
            return

        event.preventDefault()
        callback()

    return on_keydown


def register_shortcut(key: str, callback: Callable[[], None]) -> None:
    """Register a global keyboard shortcut.

    Args:
        key: Shortcut string, e.g. ``"ctrl+s"``, ``"alt+shift+g"``,
            ``"escape"``.
        callback: Zero-argument callable invoked when the shortcut is
            pressed.

    Raises:
        ValueError: If *key* is not a recognized shortcut pattern.
    """
    if not _ensure_js():
        return

    key_lower = key.lower()
    if key_lower in _registered:
        unregister_shortcut(key_lower)

    handler = _make_handler(key_lower, callback)
    if handler is None:
        return

    proxy = _create_proxy(handler)
    _window.addEventListener("keydown", proxy)

    _registered[key_lower] = {"handler": handler, "proxy": proxy}


def unregister_shortcut(key: str) -> None:
    """Remove a previously registered keyboard shortcut.

    Args:
        key: Shortcut string previously passed to
            ``register_shortcut``.
    """
    if not _ensure_js():
        return

    key_lower = key.lower()
    entry = _registered.pop(key_lower, None)
    if entry is None:
        return

    _window.removeEventListener("keydown", entry["proxy"])
    entry["proxy"].destroy()


def register_default_shortcuts(callbacks: dict[str, Callable[[], None]]) -> None:
    """Register all six default shortcuts with the provided callbacks.

    Args:
        callbacks: Mapping of action names to zero-argument callables.
            Expected keys: ``"save_session"``, ``"undo"``,
            ``"redo_shift_z"``, ``"redo_y"``, ``"mode_toggle"``,
            ``"escape"``.

    The six defaults are:
        - Ctrl+S (save_session)
        - Ctrl+Z (undo)
        - Ctrl+Shift+Z (redo_shift_z)
        - Ctrl+Y (redo_y)
        - Alt+Shift+G (mode_toggle)
        - Escape (escape)
    """
    key_map: dict[str, str] = {
        "save_session": "ctrl+s",
        "undo": "ctrl+z",
        "redo_shift_z": "ctrl+shift+z",
        "redo_y": "ctrl+y",
        "mode_toggle": "alt+shift+g",
        "escape": "escape",
    }

    for action_name, key in key_map.items():
        callback = callbacks.get(action_name)
        if callback is not None:
            register_shortcut(key, callback)


def get_shortcuts() -> dict[str, dict]:
    """Return a snapshot of all registered shortcut definitions."""
    return dict(_SHORTCUTS)


def format_shortcut(keys: list[str]) -> str:
    """Pretty-print a key combination as "Ctrl + Shift + Z".

    Args:
        keys: Ordered list of modifier / key identifiers.

    Returns:
        Human-readable shortcut string.
    """
    parts: list[str] = []
    for k in keys:
        if k == "ctrl":
            parts.append("Ctrl")
        elif k == "alt":
            parts.append("Alt")
        elif k == "shift":
            parts.append("Shift")
        else:
            parts.append(k.upper())
    return " + ".join(parts)
