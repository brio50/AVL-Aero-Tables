import sys
from importlib.metadata import version as _pkg_version
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "_ext"))

# -- Project --------------------------------------------------------------

project = "avl-aero-tables"
author = "Brian Borra"
release = _pkg_version("avl-aero-tables")

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_design",
    "plotly_figure",
]

# -- Source ---------------------------------------------------------------

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
myst_enable_extensions = ["deflist"]

# -- HTML -----------------------------------------------------------------

html_theme = "sphinx_book_theme"
html_title = "AVL Aerodynamic Tables"
html_show_copyright = False
templates_path = ["_templates"]
html_static_path = ["_static"]
html_css_files = ["custom.css"]

html_theme_options = {
    "repository_url": "https://github.com/brio50/avl-aero-tables",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "show_toc_level": 2,
}

# -- Extensions -----------------------------------------------------------

copybutton_selector = "div:not(.no-copybutton) > div.highlight > pre"

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = False
napoleon_numpy_docstring = True

# -- Dependencies for included external files ---------------------------------
# Tells Sphinx to re-read these pages when the included external file changes.

_ROOT = Path(__file__).parent.parent
_INCLUDE_DEPS = {
    "dev/changelog": _ROOT / "CHANGELOG.md",
    "dev/contributing": _ROOT / "CONTRIBUTING.md",
    "dev/license": _ROOT / "LICENSE.md",
}


def setup(app):
    app.connect("source-read", _note_include_deps)


def _note_include_deps(app, docname, source):
    if docname in _INCLUDE_DEPS:
        app.env.note_dependency(str(_INCLUDE_DEPS[docname]))
