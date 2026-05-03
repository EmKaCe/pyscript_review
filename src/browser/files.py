"""Client-side file download utilities for PyScript browser environments.

Provides three download functions that trigger file downloads entirely in
the browser — no server requests involved:

- ``download_json(data, filename)`` — serialise a Python object as a JSON file
- ``download_text(text, filename)`` — download plain text content
- ``download_blob(blob, filename)`` — download an existing JS ``Blob`` object

All functions are no-ops when the ``js`` module is unavailable (pytest, SSR).
In that case a warning is printed to stderr.
"""

from __future__ import annotations

import json
import warnings
from typing import Any


def download_blob(blob: Any, filename: str) -> None:
    """Download a JS Blob object as a file in the browser.

    Creates a temporary ``<a>`` element, sets its ``href`` to an object URL
    and its ``download`` attribute to ``filename``, clicks it programmatically,
    then revokes the object URL to prevent memory leaks.

    No-op when running outside a browser (pytest, SSR).

    Args:
        blob: A JavaScript ``Blob`` object (e.g. created via ``js.Blob.new(...)``).
        filename: The desired download filename, e.g. ``"review.json"``.

    Raises:
        TypeError: If ``blob`` is not a Blob-like object (has no ``size`` or
            ``type`` attributes detected). Only raised in browser mode.
    """
    try:
        from js import URL, document  # type: ignore[import-untyped]
    except ImportError:
        warnings.warn(
            "download_blob: js module not available (no-op outside browser)",
            stacklevel=2,
        )
        return

    url = URL.createObjectURL(blob)
    a = document.createElement("a")
    a.href = url
    a.download = filename
    a.style.display = "none"
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)


def download_text(text: str, filename: str) -> None:
    """Download a string as a text file in the browser.

    Wraps ``text`` in a ``Blob`` with MIME type ``"text/plain;charset=utf-8"``
    and triggers the download via ``download_blob``.

    No-op when running outside a browser (pytest, SSR).

    Args:
        text: The text content to download.
        filename: The desired download filename, e.g. ``"notes.txt"``.
    """
    try:
        from js import JSON, Blob  # type: ignore[import-untyped]
        from pyodide.ffi import to_js
    except ImportError:
        warnings.warn(
            "download_text: js module not available (no-op outside browser)",
            stacklevel=2,
        )
        return

    options = JSON.parse('{"type": "text/plain;charset=utf-8"}')
    blob = Blob.new(to_js([text]), options)
    download_blob(blob, filename)


def download_json(data: Any, filename: str) -> None:
    """Download a Python object as a formatted JSON file in the browser.

    Serialises ``data`` with ``indent=2`` and ``ensure_ascii=False`` for
    human-readable output, wraps it in a ``Blob``, and triggers the download.

    No-op when running outside a browser (pytest, SSR).

    Args:
        data: The Python object to serialise (must be JSON-serialisable).
        filename: The desired download filename, e.g. ``"export.json"``.

    Raises:
        TypeError: If ``data`` is not JSON-serialisable (propagated from
            ``json.dumps``). Only raised in browser mode.
    """
    try:
        from js import JSON, Blob  # type: ignore[import-untyped]
        from pyodide.ffi import to_js
    except ImportError:
        warnings.warn(
            "download_json: js module not available (no-op outside browser)",
            stacklevel=2,
        )
        return

    text = json.dumps(data, indent=2, ensure_ascii=False)
    options = JSON.parse('{"type": "application/json;charset=utf-8"}')
    blob = Blob.new(to_js([text]), options)
    download_blob(blob, filename)
