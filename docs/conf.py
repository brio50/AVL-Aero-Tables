import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

project = "avl-wrapper"
author = "Brian Borra"
release = "1.0.0"
copyright = "2026, Brian Borra"

extensions = [
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinxcontrib.mermaid",
    "sphinx_design",
]

html_theme = "sphinx_book_theme"
html_title = "avl-wrapper"
html_theme_options = {
    "repository_url": "https://github.com/brio50/avl-wrapper",
    "use_repository_button": True,
    "use_issues_button": True,
    "use_download_button": True,
}

myst_enable_extensions = ["colon_fence", "deflist"]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
html_static_path = ["_static"]
html_css_files = ["custom.css"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "numpy": ("https://numpy.org/doc/stable", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
    "matplotlib": ("https://matplotlib.org/stable", None),
}

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_typehints = "description"
napoleon_google_docstring = False
napoleon_numpy_docstring = True
