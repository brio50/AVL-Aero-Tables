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
    "sphinx_multiversion",
]

# -- Source ---------------------------------------------------------------

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]
myst_enable_extensions = ["deflist", "amsmath", "dollarmath"]
myst_heading_anchors = 3

# -- Versioned docs (sphinx-multiversion) ----------------------------------
#
# `.github/workflows/docs.yml` drives the real, multi-ref build via the
# `sphinx-multiversion` CLI, which re-invokes `sphinx-build` once per matched
# git ref, always loading THIS conf.py (from whatever ref triggered the
# workflow) but sourcing each ref's own `docs/` content — see the CLI's
# `main()`, which always passes `-c <confdir_absolute>` (the current tree)
# rather than each ref's historical confdir. That means extensions/theme
# config here apply uniformly to every built version, including old tags
# whose own `docs/conf.py` never heard of sphinx-multiversion.
#
# - `smv_tag_whitelist` matches `vX.Y.Z` release tags only; `v0.0.0-matlab`
#   (the pre-Python MATLAB baseline marker, not a real doc-worthy release)
#   is excluded because it doesn't fit the pattern.
# - `smv_branch_whitelist` + `smv_remote_whitelist` add a `master` build
#   ("latest"/in-development docs) alongside tagged releases. CI checks out
#   a detached HEAD with no local `master` branch, so the remote-tracking
#   `origin/master` ref must be whitelisted too.
# - `smv_released_pattern` must match the FULL `refs/tags/<name>` ref string
#   (not just `tags/<name>`, which is the library's own documented default
#   but never actually matches — see `sphinx_multiversion.git.get_all_refs`,
#   whose `refname` always keeps the `refs/` prefix) or every ref reports
#   `is_released=False`.
smv_tag_whitelist = r"^v\d+\.\d+\.\d+$"
smv_branch_whitelist = r"^master$"
smv_remote_whitelist = r"^origin$"
smv_released_pattern = r"^refs/tags/.*$"

# Where `docs.yml` publishes the built site; also the address the in-page
# version-switcher dropdown fetches `switcher.json` from (see below and
# `docs/_scripts/gen_switcher.py`). Kept as a plain https:// URL rather than
# a path relative to the current page so it resolves the same way regardless
# of how deep the current version's page is nested.
_PAGES_BASE_URL = "https://brio50.github.io/avl-aero-tables"

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
    # sphinx-book-theme inherits its version-switcher dropdown from
    # pydata-sphinx-theme: https://pydata-sphinx-theme.readthedocs.io/en/stable/user_guide/version-dropdown.html
    # `navbar_end` is empty by default in sphinx-book-theme's own theme.conf
    # (it overrides the pydata default), so "version-switcher" must be added
    # back explicitly or the dropdown never renders.
    "navbar_end": ["version-switcher", "theme-switcher", "navbar-icon-links"],
    "switcher": {
        "json_url": f"{_PAGES_BASE_URL}/switcher.json",
        # Placeholder; `_set_switcher_version_match` below overwrites this
        # per-build with the actual ref name (e.g. "v2.0.1", "master") once
        # sphinx-multiversion has set `smv_current_version`.
        "version_match": release,
    },
    # `switcher.json` lives at the Pages site root (written post-build by
    # `docs/_scripts/gen_switcher.py`, not by this Sphinx build itself), so
    # it can't be validated by reading a file next to this conf.py, and
    # fetching the live URL during CI would race the very deploy that
    # publishes it. Runtime fetching in the browser is unaffected.
    "check_switcher": False,
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
    # Connected here (this project's own `setup()`, which Sphinx always calls
    # last, after every extension in `extensions` has registered its own
    # hooks) so this runs AFTER sphinx_multiversion's "config-inited" handler
    # has already populated `config.smv_current_version` for the ref
    # currently being built.
    app.connect("config-inited", _set_switcher_version_match)


def _note_include_deps(app, docname, source):
    if docname in _INCLUDE_DEPS:
        app.env.note_dependency(str(_INCLUDE_DEPS[docname]))


def _set_switcher_version_match(app, config):
    """Point the version-switcher dropdown at the ref actually being built.

    Every version is built from this same conf.py (see the comment above
    `smv_tag_whitelist`), so the plain `release` module global is always the
    CURRENT tree's version, not whichever tag/branch sphinx-multiversion is
    building right now. `smv_current_version` (e.g. "v2.0.1", "master") is
    what actually varies per build, and matches the "version" values written
    into switcher.json by `docs/_scripts/gen_switcher.py`.
    """
    current_version = config.smv_current_version or release
    config.html_theme_options.setdefault("switcher", {})["version_match"] = (
        current_version
    )
