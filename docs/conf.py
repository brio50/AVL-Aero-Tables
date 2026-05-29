import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent / "_ext"))

_ROOT = Path(__file__).resolve().parent.parent
with (_ROOT / "pyproject.toml").open("rb") as _f:
    _pyproject = tomllib.load(_f)

release = str(_pyproject["project"]["version"])

# -- Project --------------------------------------------------------------

project = "avl-aero-tables"
author = "Brian Borra"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_design",
    "plotly_figure",
    "sphinx.ext.mathjax",
]

# -- Source ---------------------------------------------------------------

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
myst_enable_extensions = ["deflist", "amsmath", "dollarmath"]
myst_heading_anchors = 3

# -- HTML -----------------------------------------------------------------

html_theme = "sphinx_book_theme"
html_title = "AVL Aerodynamic Tables"
html_show_copyright = False
templates_path = ["_templates"]
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_js_files = ["custom.js"]

html_theme_options = {
    "repository_url": "https://github.com/brio50/avl-aero-tables",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
    "show_toc_level": 2,
}

# -- Extensions -----------------------------------------------------------

math_eqref_format = "Eqn. ({number})"
copybutton_selector = "div:not(.no-copybutton) > div.highlight > pre"

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = False
napoleon_numpy_docstring = True

_INCLUDE_DEPS = {
    docname: _ROOT / relpath
    for docname, relpath in _pyproject["tool"]["sphinx-build"]["include_deps"].items()
}


def setup(app):
    app.connect("source-read", _note_include_deps)


def _note_include_deps(app, docname, source):
    if docname in _INCLUDE_DEPS:
        app.env.note_dependency(str(_INCLUDE_DEPS[docname]))
