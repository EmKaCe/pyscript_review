"""SciPro Review — PyScript entry point.

This module is loaded by PyScript's ``<script type="py" src="./src/main.py">``.
It imports the pre-configured ``app`` instance from ``src.app``, which
triggers component registration, router installation, and keyboard
shortcut setup.

In test environments (pytest), the import path resolves through the
Python package namespace and works identically.
"""

import sys

# Ensure project root is on sys.path for PyScript virtual filesystem.
# When running under Pyodide, the project root may not be in sys.path
# even though pyscript.json maps all src/ files to the virtual filesystem.
if "/src" not in sys.path and "src" not in sys.path:
    sys.path.insert(0, "/")

from src.app import app  # noqa: F401 — PuePy Application instance

if __name__ == "__main__":
    pass
