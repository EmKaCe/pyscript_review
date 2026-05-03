"""Responsive breakpoint detection via matchMedia.

Provides mobile/desktop breakpoint detection using
``window.matchMedia`` with ``create_proxy`` for JS interop.

All functions are no-ops when running outside a browser
(pytest, SSR).

Breakpoint: desktop starts at 1024px (mobile is ≤1023px).
"""

from collections.abc import Callable
from typing import Any

from pyodide.ffi import create_proxy  # type: ignore[import-untyped]

_MEDIA_QUERY = "(max-width: 1023px)"
_listeners: dict[int, Any] = {}
_next_id: int = 0


def is_mobile() -> bool:
    """Check whether the viewport is currently at mobile width.

    Returns:
        ``True`` if viewport width is ≤1023px, ``False`` otherwise.
        Always returns ``False`` when running outside a browser.
    """
    try:
        from js import window  # type: ignore[import-untyped]

        mql = window.matchMedia(_MEDIA_QUERY)
        return bool(mql.matches)
    except ImportError:
        return False


def on_breakpoint_change(callback: Callable[[bool], None]) -> None:
    """Register a callback invoked when the mobile breakpoint changes.

    The callback receives a single ``bool`` argument: ``True`` for
    mobile (viewport width ≤ 1023px), ``False`` for desktop.

    Uses ``pyodide.ffi.create_proxy`` to wrap the callback for JS
    ``addEventListener``. The proxy is stored and cleaned up when
    ``remove_breakpoint_listener`` is called.

    No-op when running outside a browser.

    Args:
        callback: Function taking one ``bool`` parameter, called on
            breakpoint transition.

    Raises:
        ValueError: If the callback has already been registered.
    """
    global _next_id  # noqa: PLW0603

    try:
        from js import window  # type: ignore[import-untyped]
    except ImportError:
        return

    cb_id = id(callback)
    if cb_id in _listeners:
        raise ValueError("This callback is already registered as a breakpoint listener.")

    def _handler(event: Any) -> None:
        callback(bool(event.matches))

    proxy = create_proxy(_handler)
    _listeners[cb_id] = proxy
    _next_id += 1

    mql = window.matchMedia(_MEDIA_QUERY)
    mql.addEventListener("change", proxy)


def remove_breakpoint_listener(callback: Callable[[bool], None]) -> None:
    """Unregister a previously registered breakpoint change callback.

    Removes the listener from ``matchMedia`` and destroys the
    ``create_proxy`` wrapper.

    No-op when running outside a browser.

    Args:
        callback: The same function reference passed to
            ``on_breakpoint_change``.

    Raises:
        ValueError: If the callback was not registered.
    """
    try:
        from js import window  # type: ignore[import-untyped]
    except ImportError:
        return

    cb_id = id(callback)
    proxy = _listeners.pop(cb_id, None)

    if proxy is None:
        raise ValueError("Callback was not registered as a breakpoint listener.")

    mql = window.matchMedia(_MEDIA_QUERY)
    mql.removeEventListener("change", proxy)
    proxy.destroy()
