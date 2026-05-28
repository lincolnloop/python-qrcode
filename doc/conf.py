"""Sphinx configuration for python-qrcode API documentation."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

project = "python-qrcode"
copyright = "2025, Lincoln Loop"  # noqa: A001
author = "Lincoln Loop"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path: list[str] = []

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

napoleon_google_docstring = True
napoleon_include_init_with_doc = True
