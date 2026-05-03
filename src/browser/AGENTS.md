# src/browser — JS INTEROP SHIMS

## OVERVIEW

Pyodide FFI bridge layer: IndexedDB storage, BasecoatBridge, theme controller, timer manager, files, shortcuts, responsive. 8 modules, 1769 lines.

## STRUCTURE

| File | Lines | Role |
|------|-------|------|
| `storage.py` | 926 | `StorageBackend` ABC + `BrowserStorage` (IndexedDB) + `MemoryStorage` (tests) |
| `shortcuts.py` | 233 | Keyboard shortcut registry + format helpers |
| `theme_controller.py` | ~100 | Dark/light theme toggle via Basecoat CSS |
| `basecoat_bridge.py` | ~50 | `window.basecoat.initAll()` wrapper after PuePy redraws |
| `files.py` | ~100 | Download/upload JSON via browser File API |
| `timer_manager.py` | ~80 | `setTimeout`/`clearTimeout` wrapper, no-op outside browser |
| `responsive.py` | ~50 | Breakpoint detection, mobile view toggle |

## CONVENTIONS

- **`create_proxy` required**: ALL raw JS event listeners use `pyodide.ffi.create_proxy`; call `.destroy()` in cleanup.
- **BasecoatBridge**: Call `window.basecoat.initAll()` only after PuePy page transitions, NOT on every redraw.
- **Storage ABC pattern**: `StorageBackend` defines interface; `BrowserStorage` (IndexedDB) for production, `MemoryStorage` for tests.
- **No-op degradation**: TimerManager and other browser-dependent modules detect absent JS APIs and become no-ops.
- **Async IndexedDB**: All `store.put`/`get`/`delete` operations use success/error proxies + `asyncio.Event`.

## NOTABLE

- `storage.py:import_all` is fire-and-forget (unlike all other methods) — proxies destroyed before IndexedDB commits complete.
- BasecoatBridge: Do NOT call `initAll()` on every redraw — only after page transitions or targeted component creation.
