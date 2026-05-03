"""Timer management via ``window.setTimeout`` with safe cleanup.

Wraps JavaScript ``setTimeout`` / ``clearTimeout`` with
``pyodide.ffi.create_proxy`` so that callbacks are properly tracked
and can be destroyed on cleanup.

All methods are safe no-ops when running outside a browser
(pytest, SSR).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


class TimerManager:
    """Manage ``window.setTimeout`` timers with ``create_proxy`` wrapping.

    Each timer callback is wrapped in a ``create_proxy`` to ensure
    proper lifecycle in Pyodide. Timers are tracked by their JS timer
    ID so they can be individually or bulk-cancelled.

    Example::

        mgr = TimerManager()
        tid = mgr.set_timeout(lambda: print("hi"), 1000)
        # ...
        mgr.clear_timeout(tid)
        # or
        mgr.clear_all()
    """

    def __init__(self) -> None:
        """Initialise the timer manager.

        Attempts to import ``window`` and ``create_proxy``. When
        running outside a browser (pytest, SSR) all methods become
        no-ops.
        """
        self._timers: dict[int, Any] = {}
        self._window: Any = None
        self._create_proxy: Any = None

        try:
            from js import window  # type: ignore[import-untyped]
            from pyodide.ffi import create_proxy  # type: ignore[import-untyped]

            self._window = window
            self._create_proxy = create_proxy
        except ImportError:
            pass

    def set_timeout(self, callback: Callable[[], None], ms: int) -> int:
        """Schedule *callback* to run after *ms* milliseconds.

        Wraps *callback* in ``create_proxy`` so Pyodide can call it
        safely, then passes the proxy to ``window.setTimeout``. The
        proxy and timer ID are tracked for later cleanup.

        No-op when running outside a browser (returns 0).

        Args:
            callback: Zero-argument callable to invoke after the
                delay.
            ms: Delay in milliseconds.

        Returns:
            The numeric timer ID (usable with ``clear_timeout``), or
            ``0`` if the browser environment is unavailable.
        """
        if self._window is None or self._create_proxy is None:
            return 0

        proxy = self._create_proxy(callback)
        timer_id = self._window.setTimeout(proxy, ms)
        # timer_id is a JavaScript number; convert to Python int.
        timer_id_int = int(timer_id)
        self._timers[timer_id_int] = proxy
        return timer_id_int

    def clear_timeout(self, timer_id: int) -> None:
        """Cancel a specific timer and destroy its proxy.

        Removes the timer from the tracking dictionary, calls
        ``window.clearTimeout``, and destroys the associated
        ``create_proxy``.

        No-op when running outside a browser or if *timer_id* is
        unknown.

        Args:
            timer_id: The numeric timer ID returned by
                ``set_timeout``.
        """
        if self._window is None:
            return

        proxy = self._timers.pop(timer_id, None)
        if proxy is None:
            return

        self._window.clearTimeout(timer_id)
        proxy.destroy()

    def clear_all(self) -> None:
        """Cancel all active timers and destroy all proxies.

        Iterates every tracked timer, calls
        ``window.clearTimeout``, and destroys the associated
        ``create_proxy`` wrapper. Clears the internal tracker
        afterwards.

        No-op when running outside a browser.
        """
        if self._window is None:
            return

        for timer_id, proxy in self._timers.items():
            self._window.clearTimeout(timer_id)
            proxy.destroy()

        self._timers.clear()
