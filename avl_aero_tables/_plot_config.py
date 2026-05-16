"""Shared plotly defaults for all avl_aero_tables figures."""

# Applied to every axis in every 3-D scene.
AXIS_3D: dict = dict(showbackground=False)

# Camera for the geometry figure: nose-left, flying toward viewer.
CAMERA_GEOM: dict = dict(eye=dict(x=-1.5, y=-1.5, z=0.8))

# Surface appearance for aero coefficient plots.
COLORSCALE_STAB = "Viridis"
COLORSCALE_CTRL = "Plasma"
OPACITY_SURFACE = 0.9
