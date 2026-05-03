import os
import sys

# Path setup to allow imports from the project root
sys.path.insert(0, os.path.abspath(".."))

# Mock pyodide for autodoc
from unittest.mock import MagicMock

mock_pyodide = MagicMock()
sys.modules["pyodide"] = mock_pyodide
sys.modules["pyodide.ffi"] = mock_pyodide.ffi

project = "SciPro Review"
copyright = "2026, SciPro Team"
author = "SciPro Team"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_design",
]

# MyST Configuration
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "shibuya"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_logo = "_static/logo.svg"

html_theme_options = {
    "nav_links": [
        {"title": "App Home", "url": "/"},
        {"title": "Review", "url": "/#/review"},
        {"title": "Settings", "url": "/#/settings"},
    ],
    "github_url": "https://github.com/ohmyopen-code/scipro",
    "accent_color": "blue",
    "globaltoc_expand_depth": 2,
    "light_logo": "_static/logo.svg",
    "dark_logo": "_static/logo.svg",
}

# Add any custom options here
html_title = "SciPro Review"
html_short_title = "SciPro"


# Autodoc settings
autoclass_content = "both"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

# MyST-Parser settings (allow both .rst and .md)
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

python_use_unqualified_type_names = True
