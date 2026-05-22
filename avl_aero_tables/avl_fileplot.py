"""Plot AVL geometry as an interactive 3-D plotly figure."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from avl_aero_tables._plot_config import AXIS_3D, CAMERA_GEOM, equal_3d_ranges
from avl_aero_tables.avl_fileread import AvlBody, AvlGeometry, AvlSurface

if TYPE_CHECKING:
    import plotly.graph_objects as go


def _trans(surf_or_body: AvlSurface | AvlBody) -> tuple[float, float, float]:
    t = surf_or_body.trans
    if t is None or len(t) < 3:
        return 0.0, 0.0, 0.0
    return float(t[0]), float(t[1]), float(t[2])


def _build_traces(geometry: AvlGeometry) -> list[dict[str, Any]]:
    """Return geometry as trace-spec dicts (mode, x, y, z, color, width/size)."""
    hdr = geometry.header
    traces: list[dict[str, Any]] = []

    traces.append(dict(
        mode="markers", x=[hdr.Xref], y=[hdr.Yref], z=[hdr.Zref],
        color="black", size=8,
    ))

    if geometry.body is not None:
        body = geometry.body
        xt, yt, zt = _trans(body)
        xb = np.array(body.bfile_x) + xt
        yb = np.array(body.bfile_y) + yt
        n = len(xb)
        if n >= 2:
            zb = np.full(n, zt)
            half = n // 2
            cl_x = xb[:half]
            traces.append(dict(
                mode="lines", x=list(xb), y=list(yb), z=list(zb),
                color="green", width=1,
            ))
            traces.append(dict(
                mode="lines",
                x=list(cl_x), y=list(np.full(half, yt)), z=list(np.full(half, zt)),
                color="red", width=1,
            ))
            for i in range(0, half, 2):
                r = (abs(yb[i]) + abs(yb[n - 1 - i])) / 2.0
                theta = np.linspace(0, 2 * np.pi, 33)
                traces.append(dict(
                    mode="lines",
                    x=list(np.full_like(theta, cl_x[i])),
                    y=list(yt + r * np.cos(theta)),
                    z=list(zt + r * np.sin(theta)),
                    color="mediumpurple", width=1,
                ))

    for surf in geometry.surface.values():
        sections = surf.sections
        n_sec = len(sections)
        if n_sec == 0:
            continue
        xt, yt, zt = _trans(surf)
        sc = surf.scale or [1.0, 1.0, 1.0]
        sx, sy, sz = float(sc[0]), float(sc[1]), float(sc[2])
        dainc = surf.dainc or 0.0
        mirror = isinstance(surf.ydupl, float) and surf.ydupl == 0.0

        x_le = np.array([s.xle for s in sections]) * sx + xt
        y_le = np.array([s.yle for s in sections]) * sy + yt
        z_le = np.array([s.zle for s in sections]) * sz + zt
        chord = np.array([s.chord for s in sections]) * sx
        ainc = np.array([s.ainc for s in sections]) + dainc
        x_te = x_le + chord
        z_te = z_le + chord * np.sin(np.radians(ainc))

        for k in range(n_sec):
            traces.append(dict(
                mode="lines",
                x=[x_le[k], x_te[k]], y=[y_le[k], y_le[k]], z=[z_le[k], z_te[k]],
                color="mediumpurple", width=1,
            ))
            if mirror:
                traces.append(dict(
                    mode="lines",
                    x=[x_le[k], x_te[k]], y=[-y_le[k], -y_le[k]], z=[z_le[k], z_te[k]],
                    color="mediumpurple", width=1,
                ))

        traces.append(dict(
            mode="lines", x=list(x_le), y=list(y_le), z=list(z_le),
            color="steelblue", width=2,
        ))
        traces.append(dict(
            mode="lines", x=list(x_te), y=list(y_le), z=list(z_te),
            color="steelblue", width=2,
        ))
        if mirror:
            traces.append(dict(
                mode="lines", x=list(x_le), y=list(-y_le), z=list(z_le),
                color="steelblue", width=2,
            ))
            traces.append(dict(
                mode="lines", x=list(x_te), y=list(-y_le), z=list(z_te),
                color="steelblue", width=2,
            ))

    return traces


def avl_fileplot(geometry: AvlGeometry) -> "go.Figure":
    """Plot AVL geometry as a single interactive 3-D figure.

    Parameters
    ----------
    geometry:
        Parsed AvlGeometry from avl_fileread().

    Returns
    -------
    plotly.graph_objects.Figure
        Interactive 3-D figure. Save with ``fig.write_html("out.html")``;
        embed in Sphinx via the ``plotly-figure`` directive.

    Example
    -------
    >>> from avl_aero_tables.avl_fileread import avl_fileread
    >>> from avl_aero_tables.avl_fileplot import avl_fileplot
    >>> geom = avl_fileread("examples/bd/bd.avl")
    >>> fig = avl_fileplot(geom)
    >>> "Bubble Dancer" in fig.layout.title.text
    True
    >>> fig.write_html(
    ...     "geometry.html", include_plotlyjs="cdn", config={"displayModeBar": True}
    ... )
    """
    import plotly.graph_objects as go

    traces = _build_traces(geometry)

    axis_ranges = equal_3d_ranges(
        [v for t in traces for v in t["x"]],
        [v for t in traces for v in t["y"]],
        [v for t in traces for v in t["z"]],
    )
    arrow = (axis_ranges[0][1] - axis_ranges[0][0]) / 2 * 0.20

    fig = go.Figure()
    for t in traces:
        if t["mode"] == "lines":
            fig.add_trace(go.Scatter3d(
                x=t["x"], y=t["y"], z=t["z"],
                mode="lines",
                line=dict(color=t["color"], width=t.get("width", 1)),
                showlegend=False,
            ))
        else:
            fig.add_trace(go.Scatter3d(
                x=t["x"], y=t["y"], z=t["z"],
                mode="markers",
                marker=dict(color=t["color"], size=t.get("size", 6)),
                showlegend=False,
            ))

    hdr = geometry.header

    # Legend proxies — one entry per triad
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None], mode="markers",
        marker=dict(color="slategray", size=6, symbol="square"),
        name="AVL frame (origin)", showlegend=True,
    ))
    fig.add_trace(go.Scatter3d(
        x=[None], y=[None], z=[None], mode="markers",
        marker=dict(color="black", size=6),
        name="Body frame (CG)", showlegend=True,
    ))

    _add_triad(fig, arrow,
               origin=(0.0, 0.0, 0.0),
               axes=[
                   ((1, 0, 0), "slategray", "X"),
                   ((0, 1, 0), "slategray", "Y"),
                   ((0, 0, 1), "slategray", "Z"),
               ])

    # Aircraft body-frame triad at CG: +x nose, +y right wing, +z down
    # AVL convention: X increases aft, Y starboard, Z up → body axes are -X, +Y, -Z
    _add_triad(fig, arrow,
               origin=(hdr.Xref, hdr.Yref, hdr.Zref),
               axes=[
                   ((-1, 0, 0), "red",   "x<sub>b</sub>"),
                   (( 0, 1, 0), "green", "y<sub>b</sub>"),
                   (( 0, 0,-1), "blue",  "z<sub>b</sub>"),
               ])

    _up_z = dict(x=0, y=0, z=1)
    _up_x = dict(x=1, y=0, z=0)  # top-view: nose toward bottom (+X aft → nose down)
    _cam = "scene.camera"
    _view_buttons = [
        dict(label="Iso",   method="relayout",
             args=[{_cam: {"eye": dict(x=-1.5, y=1.5, z=0.8), "up": _up_z}}]),
        dict(label="Right", method="relayout",
             args=[{_cam: {"eye": dict(x=0.0,  y=2.5,  z=0.0), "up": _up_z}}]),
        dict(label="Front", method="relayout",
             args=[{_cam: {"eye": dict(x=-2.5, y=0.0,  z=0.0), "up": _up_z}}]),
        dict(label="Top",   method="relayout",
             args=[{_cam: {"eye": dict(x=0.0,  y=0.0,  z=2.5), "up": _up_x}}]),
    ]

    fig.update_layout(
        title=dict(text=geometry.header.name, x=0.5, xanchor="center"),
        height=700,
        showlegend=True,
        legend=dict(x=0.01, y=0.09, xanchor="left", yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.6)", borderwidth=0),
        margin=dict(l=0, r=0, t=40, b=10),
        modebar=dict(
            orientation="v",
            bgcolor="rgba(255,255,255,0.6)",
            color="#666",
            activecolor="#2563eb",
        ),
        scene=dict(
            domain=dict(y=[0.07, 1.0]),
            aspectmode="manual",
            aspectratio=dict(x=1, y=1, z=1),
            xaxis=dict(title="X", range=axis_ranges[0], **AXIS_3D),
            yaxis=dict(title="Y", range=axis_ranges[1], **AXIS_3D),
            zaxis=dict(title="Z", range=axis_ranges[2], **AXIS_3D),
            camera=CAMERA_GEOM,
        ),
        updatemenus=[dict(
            type="buttons",
            direction="right",
            showactive=False,
            x=0.5,
            xanchor="center",
            y=0.06,
            yanchor="top",
            buttons=_view_buttons,
        )],
    )

    return fig


def _add_triad(
    fig: "go.Figure",
    length: float,
    origin: tuple[float, float, float],
    axes: list[tuple[tuple[float, float, float], str, str]],
) -> None:
    """Add a coordinate triad (shaft + cone arrowhead) to a 3-D figure."""
    import plotly.graph_objects as go

    ox, oy, oz = origin
    for (dx, dy, dz), color, label in axes:
        tx, ty, tz = ox + dx * length, oy + dy * length, oz + dz * length
        # Label at 1.4× — past the cone tip so the arrowhead doesn't cover it
        lx = ox + dx * length * 1.8
        ly = oy + dy * length * 1.8
        lz = oz + dz * length * 1.8
        fig.add_trace(go.Scatter3d(
            x=[ox, tx], y=[oy, ty], z=[oz, tz],
            mode="lines",
            line=dict(color=color, width=3),
            showlegend=False,
        ))
        fig.add_trace(go.Cone(
            x=[tx], y=[ty], z=[tz],
            u=[dx], v=[dy], w=[dz],
            colorscale=[[0, color], [1, color]],
            showscale=False,
            sizemode="absolute",
            sizeref=length * 0.35,
            anchor="tail",
        ))
        fig.add_trace(go.Scatter3d(
            x=[lx], y=[ly], z=[lz],
            mode="text",
            text=[label],
            textfont=dict(color=color, size=13),
            textposition="middle center",
            showlegend=False,
        ))
