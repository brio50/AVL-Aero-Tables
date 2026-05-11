"""Plot AVL geometry using matplotlib (port of avl_fileplot.m)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from avl_wrapper.avl_fileread import AvlBody, AvlGeometry, AvlSurface

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


def _trans(surf_or_body: AvlSurface | AvlBody) -> tuple[float, float, float]:
    t = surf_or_body.trans
    if t is None or len(t) < 3:
        return 0.0, 0.0, 0.0
    return float(t[0]), float(t[1]), float(t[2])


def _plot_on(axes: list, geometry: AvlGeometry) -> None:
    """Draw all geometry elements on every axes in *axes*."""

    hdr = geometry.header

    for ax in axes:
        ax.scatter(
            [hdr.Xref],
            [hdr.Yref],
            [hdr.Zref],
            s=60,
            c="k",
            zorder=5,
            label="CG",
        )

    # Body (fuselage)
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
            cl_y = np.full(half, yt)
            cl_z = np.full(half, zt)
            for ax in axes:
                ax.plot(xb, yb, zb, "-g", linewidth=0.8, label="body_line")
                ax.plot(cl_x, cl_y, cl_z, "-r", linewidth=0.8, label="center_line")
                for i in range(0, half, 2):
                    r = (abs(yb[i]) + abs(yb[n - 1 - i])) / 2.0
                    theta = np.linspace(0, 2 * np.pi, 33)
                    xs = np.full_like(theta, cl_x[i])
                    ys = cl_y[i] + r * np.cos(theta)
                    zs = cl_z[i] + r * np.sin(theta)
                    ax.plot(xs, ys, zs, "-m", linewidth=0.5)

    # Lifting surfaces
    for surf in geometry.surface.values():
        sections = surf.sections
        n_sec = len(sections)
        if n_sec == 0:
            continue
        xt, yt, zt = _trans(surf)
        dainc = surf.dainc or 0.0
        mirror = isinstance(surf.ydupl, float) and surf.ydupl == 0.0

        x_le = np.array([s.xle for s in sections]) + xt
        y_le = np.array([s.yle for s in sections]) + yt
        z_le = np.array([s.zle for s in sections]) + zt
        chord = np.array([s.chord for s in sections])
        ainc = np.array([s.ainc for s in sections]) + dainc
        x_te = x_le + chord
        z_te = z_le + chord * np.sin(np.radians(ainc))

        for ax in axes:
            for k in range(n_sec):
                ax.plot(
                    [x_le[k], x_te[k]],
                    [y_le[k], y_le[k]],
                    [z_le[k], z_te[k]],
                    "-m",
                    linewidth=0.5,
                )
                if mirror:
                    ax.plot(
                        [x_le[k], x_te[k]],
                        [-y_le[k], -y_le[k]],
                        [z_le[k], z_te[k]],
                        "-m",
                        linewidth=0.5,
                    )
            ax.plot(x_le, y_le, z_le, "-g", linewidth=1.2)
            ax.plot(x_te, y_le, z_te, "-g", linewidth=1.2)
            if mirror:
                ax.plot(x_le, -y_le, z_le, "-g", linewidth=1.2)
                ax.plot(x_te, -y_le, z_te, "-g", linewidth=1.2)


def avl_fileplot(geometry: AvlGeometry) -> plt.Figure:
    """Plot AVL geometry in four views: isometric, top, front, and side.

    Parameters
    ----------
    geometry:
        Parsed AvlGeometry from avl_fileread().

    Returns
    -------
    matplotlib.figure.Figure
        Figure with four 3-D subplot panels.

    Example
    -------
    >>> from avl_wrapper.avl_fileread import avl_fileread
    >>> from avl_wrapper.avl_fileplot import avl_fileplot
    >>> geom = avl_fileread("examples/bd.avl")
    >>> fig = avl_fileplot(geom)
    >>> fig.get_axes()[0].get_title()
    'Isometric'
    >>> fig.savefig("geometry.png")
    """
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 — registers projection

    fig = plt.figure(figsize=(12, 10))
    fig.suptitle(geometry.header.name)

    view_specs = [
        ("Isometric", 30.0, -37.5),
        ("Top", 90.0, -90.0),
        ("Front", 0.0, 90.0),
        ("Side", 0.0, 0.0),
    ]
    axes = []
    for idx, (title, elev, azim) in enumerate(view_specs, start=1):
        ax = fig.add_subplot(2, 2, idx, projection="3d")
        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z")
        ax.view_init(elev=elev, azim=azim)
        axes.append(ax)

    _plot_on(axes, geometry)

    for ax in axes:
        ax.set_box_aspect([1, 1, 1])

    fig.tight_layout()
    return fig
