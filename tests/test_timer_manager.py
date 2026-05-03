"""Tests for TimerManager — browser-independent no-op behavior.

In pytest (no PyScript/browser), TimerManager catches ImportError and
all methods become safe no-ops. These tests verify that contract.
"""

from __future__ import annotations

from src.browser.timer_manager import TimerManager


class TestTimerManagerInstantiation:
    """TimerManager can be instantiated without a browser."""

    def test_instantiates_without_browser(self) -> None:
        """TimerManager should not raise ImportError when no browser is available."""
        mgr = TimerManager()
        assert mgr is not None

    def test_window_is_none_outside_browser(self) -> None:
        """_window should be None when js module is unavailable."""
        mgr = TimerManager()
        assert mgr._window is None

    def test_create_proxy_is_none_outside_browser(self) -> None:
        """_create_proxy should be None when pyodide.ffi is unavailable."""
        mgr = TimerManager()
        assert mgr._create_proxy is None


class TestTimerManagerSetTimeout:
    """set_timeout() returns 0 when no browser (no-op mode)."""

    def test_set_timeout_returns_zero(self) -> None:
        """set_timeout should return 0 in no-op mode."""
        mgr = TimerManager()
        result = mgr.set_timeout(lambda: None, 1000)
        assert result == 0

    def test_set_timeout_does_not_crash(self) -> None:
        """set_timeout with a valid callback should not raise."""
        mgr = TimerManager()
        mgr.set_timeout(lambda: print("test"), 500)

    def test_set_timeout_zero_ms(self) -> None:
        """set_timeout with ms=0 should also return 0 in no-op mode."""
        mgr = TimerManager()
        assert mgr.set_timeout(lambda: None, 0) == 0


class TestTimerManagerClearTimeout:
    """clear_timeout() doesn't crash when no browser."""

    def test_clear_timeout_no_crash(self) -> None:
        """clear_timeout should silently do nothing in no-op mode."""
        mgr = TimerManager()
        mgr.clear_timeout(0)

    def test_clear_timeout_unknown_id(self) -> None:
        """clear_timeout with an unknown timer ID should not raise."""
        mgr = TimerManager()
        mgr.clear_timeout(99999)

    def test_clear_timeout_negative_id(self) -> None:
        """clear_timeout with negative ID should not raise."""
        mgr = TimerManager()
        mgr.clear_timeout(-1)


class TestTimerManagerClearAll:
    """clear_all() doesn't crash when no browser."""

    def test_clear_all_no_crash(self) -> None:
        """clear_all should silently do nothing in no-op mode."""
        mgr = TimerManager()
        mgr.clear_all()

    def test_clear_all_after_set_timeout(self) -> None:
        """clear_all after no-op set_timeout should not raise."""
        mgr = TimerManager()
        mgr.set_timeout(lambda: None, 1000)
        mgr.clear_all()

    def test_timers_dict_empty_after_noop(self) -> None:
        """Internal _timers dict should remain empty in no-op mode."""
        mgr = TimerManager()
        mgr.set_timeout(lambda: None, 1000)
        mgr.clear_all()
        assert mgr._timers == {}
