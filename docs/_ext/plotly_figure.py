"""Sphinx extension: ``plotly-figure`` directive.

Embeds a plotly HTML file as a lazy-loading iframe.

Each file in ``_static/html/`` is a self-contained plotly figure written with
``include_plotlyjs='cdn', full_html=False``.  Using iframes keeps each figure
isolated (its own JS context, its own CDN load) and avoids embedding megabytes
of inline JSON into the parent page.  ``loading="lazy"`` defers off-screen
figures — hidden tab panels and below-the-fold plots load only when clicked.

Usage in MyST markdown::

    ```{plotly-figure} _static/html/b737_geometry.html
    :height: 500px
    :class: my-figure wide-figure
    ```

Options
-------
height : str, optional
    CSS height value applied as an inline style (e.g. ``800px``, ``60vh``).
    Defaults to ``800px``.
class : str, optional
    Space-separated CSS class names appended to ``plotly-iframe``.

The path is relative to the Sphinx source directory (``docs/``).
"""

from __future__ import annotations

import os
import pathlib
import re
from pathlib import PurePosixPath

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from sphinx.application import Sphinx


class PlotlyFigure(Directive):
    required_arguments = 1
    optional_arguments = 0
    has_content = False
    option_spec = {
        "height": directives.unchanged,
        "class": directives.unchanged,
    }

    def run(self) -> list:
        env = self.state.document.settings.env
        src = PurePosixPath(self.arguments[0].strip())

        # Relative path from the output HTML file to the figure file.
        # env.docname is e.g. "user/quickstart" (no extension).
        doc_dir = PurePosixPath(env.docname).parent  # "user"
        rel = PurePosixPath(os.path.relpath(str(src), str(doc_dir)))

        # Auto-detect height from the Plotly layout JSON baked into the file,
        # falling back to 800px. The :height: option overrides either.
        if "height" in self.options:
            height = self.options["height"]
        else:
            abs_src = pathlib.Path(env.srcdir) / str(src)
            height = "800px"
            try:
                matches = re.findall(r'"height"\s*:\s*(\d+)', abs_src.read_text())
                if matches:
                    height = f"{matches[-1]}px"
            except OSError:
                pass

        extra_classes = self.options.get("class", "")
        css_classes = ("plotly-iframe " + extra_classes).strip()

        html = (
            f'<iframe src="{rel}" width="100%"'
            f' class="{css_classes}"'
            f' style="border:none; display:block; height:{height}; overflow:hidden;"'
            ' loading="lazy"></iframe>'
        )
        return [nodes.raw("", html, format="html")]


def setup(app: Sphinx) -> dict:
    app.add_directive("plotly-figure", PlotlyFigure)
    return {"version": "0.2", "parallel_read_safe": True, "parallel_write_safe": True}
