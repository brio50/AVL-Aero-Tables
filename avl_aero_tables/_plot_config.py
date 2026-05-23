"""Shared plotly defaults and utilities for all avl_aero_tables figures."""

from __future__ import annotations

from typing import Any


def equal_3d_ranges(
    xs: list[float], ys: list[float], zs: list[float]
) -> list[list[float]]:
    """Return cubic equal-axis ranges for a 3-D scene.

    Given flat coordinate lists for each axis, computes [min, max] ranges
    that form a cube — same span on all three axes, centred on the data.
    Pass the result to Plotly's ``scene.xaxis.range`` etc. together with
    ``aspectmode="manual", aspectratio=dict(x=1, y=1, z=1)``.
    """
    coords = [xs, ys, zs]
    mins = [min(c) for c in coords]
    maxs = [max(c) for c in coords]
    half = max(hi - lo for lo, hi in zip(mins, maxs)) / 2
    mids = [(lo + hi) / 2 for lo, hi in zip(mins, maxs)]
    return [[mid - half, mid + half] for mid in mids]


# Applied to every axis in every 3-D scene.
AXIS_3D: dict[str, Any] = dict(
    showbackground=False,
    gridcolor="#d0d0d0",
    linecolor="#aaaaaa",
    zerolinecolor="#d0d0d0",
)

# Camera for the geometry figure: nose-left, flying toward viewer.
CAMERA_GEOM: dict[str, Any] = dict(
    eye=dict(x=-1.5, y=1.5, z=0.8), up=dict(x=0, y=0, z=1)
)

# Camera for aero surface plots: isometric view from front-right above.
CAMERA_AERO: dict[str, Any] = dict(eye=dict(x=1.8, y=1.8, z=1.2))


# Surface appearance for aero coefficient plots.
COLORSCALE_STAB = "Viridis"
COLORSCALE_CTRL = "Plasma"
OPACITY_SURFACE = 0.9

# Axis labels for aero surface plots.
LABEL_ALPHA = "α (deg)"
LABEL_BETA = "β (deg)"


def label_delta(surface: str) -> str:
    """Return the y-axis label for a control surface deflection axis."""
    return f"δ_{surface} (deg)"
