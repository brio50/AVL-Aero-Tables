"""Sphinx extension: ``plotly-figure`` directive.

Embeds a plotly HTML file as a lazy-loading iframe.

Each file in ``_static/html/`` is a self-contained plotly figure written with
``include_plotlyjs='cdn', full_html=False``.  Using iframes keeps each figure
isolated (its own JS context, its own CDN load) and avoids embedding megabytes
of inline JSON into the parent page.  ``loading="lazy"`` defers off-screen
figures — hidden tab panels and below-the-fold plots load only when clicked.

Usage in MyST markdown::

    ```{plotly-figure} _static/html/b737_geometry.html
    ```

The path is relative to the Sphinx source directory (``docs/``).
"""

from __future__ import annotations

import os
from pathlib import PurePosixPath

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx.application import Sphinx


class PlotlyFigure(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False

    def run(self) -> list:
        env = self.state.document.settings.env
        src = PurePosixPath(self.arguments[0].strip())

        # Relative path from the output HTML file to the figure file.
        # env.docname is e.g. "user/quickstart" (no extension).
        doc_dir = PurePosixPath(env.docname).parent  # "user"
        rel = PurePosixPath(os.path.relpath(str(src), str(doc_dir)))

        onload = (
            "var d=this.contentDocument;"
            "d.body.style.margin='0';"
            "d.body.style.overflow='hidden';"
            "this.style.height=d.body.scrollHeight+'px';"
        )
        html = (
            f'<iframe src="{rel}" width="100%"'
            f' onload="{onload}"'
            ' class="plotly-iframe"'
            ' style="border:none; display:block; min-height:450px;"'
            ' loading="lazy"></iframe>'
        )
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict:
    app.add_directive("plotly-figure", PlotlyFigure)
    return {"version": "0.1", "parallel_read_safe": True, "parallel_write_safe": True}
