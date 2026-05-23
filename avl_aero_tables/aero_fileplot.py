"""Plot AeroDatabase tables as interactive 3-D plotly surface figures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from avl_aero_tables._plot_config import (
    AXIS_3D,
    CAMERA_AERO,
    COLORSCALE_CTRL,
    COLORSCALE_STAB,
    LABEL_ALPHA,
    LABEL_BETA,
    OPACITY_SURFACE,
    label_delta,
)
from avl_aero_tables.aero_filewrite import COEF_NAMES, AeroDatabase

# Display labels for each coefficient (standard aerospace notation)
_COEF_LABEL: dict[str, str] = {
    "CLtot": "CL",
    "CYtot": "CY",
    "CDtot": "CD",
    "Cltot": "Cl",
    "Cmtot": "Cm",
    "Cntot": "Cn",
}

if TYPE_CHECKING:
    import plotly.graph_objects as go



def aero_fileplot(
    aero: AeroDatabase,
    beta_ref: float = 0.0,
) -> "list[go.Figure]":
    """Plot stability and control coefficient tables from an AeroDatabase.

    Produces two sets of interactive figures:

    1. **Stability figure** — grid of 3-D surface plots showing each of the
       six total-force coefficients vs. alpha and beta.

    2. **Control figures** — one figure per coefficient, each containing one
       subplot per control surface, showing the coefficient vs. alpha and
       deflection at *beta_ref*.

    Parameters
    ----------
    aero:
        AeroDatabase built by aero_filewrite().
    beta_ref:
        Sideslip angle (deg) at which control-surface subplots are sliced.
        The nearest available beta breakpoint is used.

    Returns
    -------
    list[plotly.graph_objects.Figure]
        Stability figure first, then one control figure per coefficient.
        Save with ``fig.write_html("out.html")``; embed in Sphinx via the
        ``plotly-figure`` directive.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import aero_fileplot
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         ctrl_sweeps={"elevator": [-10, 0, 10]},
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = aero_fileplot(db)
    >>> len(figs)
    7
    >>> figs[0].layout.title.text
    'Stability coefficients'
    >>> figs[1].layout.title.text
    'CLtot  (β = 0.0°)'
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figs: list[go.Figure] = []

    # ------------------------------------------------------------------
    # 1. Stability figure
    # ------------------------------------------------------------------
    stab_coefs = [c for c in COEF_NAMES if c in aero.stab]
    if stab_coefs:
        n_cols = 3
        n_rows = (len(stab_coefs) + n_cols - 1) // n_cols
        fig_stab = make_subplots(
            rows=n_rows, cols=n_cols,
            specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
            subplot_titles=list(stab_coefs),
            vertical_spacing=0.12,
            horizontal_spacing=0.01,
        )
        n_scenes = n_rows * n_cols
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_scenes)]
        for i, coef in enumerate(stab_coefs):
            tbl = aero.stab[coef]
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            fig_stab.add_trace(
                go.Surface(
                    x=alpha_g, y=beta_g, z=tbl.data,
                    colorscale=COLORSCALE_STAB, opacity=OPACITY_SURFACE,
                    showscale=False, name=coef,
                ),
                row=i // n_cols + 1, col=i % n_cols + 1,
            )
            fig_stab.update_layout(**{scene_names[i]: dict(
                aspectmode="cube",
                camera=CAMERA_AERO,
                xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                yaxis=dict(title=LABEL_BETA, **AXIS_3D),
                zaxis=dict(title=_COEF_LABEL[coef], **AXIS_3D),
            )})
        fig_stab.update_layout(
            title=dict(
                text="Stability coefficients",
                x=0.5, xanchor="center", y=0.99, yanchor="top",
            ),
            height=330 * n_rows,
            showlegend=False,
            margin=dict(l=30, r=30, t=55, b=20),
            modebar=dict(
                orientation="v",
                bgcolor="rgba(255,255,255,0.6)",
                color="#666",
                activecolor="#2563eb",
            ),
        )
        figs.append(fig_stab)

    # ------------------------------------------------------------------
    # 2. Control figures
    # ------------------------------------------------------------------
    ctrl_surfaces = list(dict.fromkeys(t.surface for t in aero.ctrl.values()))
    if not ctrl_surfaces:
        return figs

    sample_tbl = next(iter(aero.ctrl.values()))
    beta_arr = sample_tbl.beta
    bi = int(np.argmin(np.abs(beta_arr - beta_ref)))
    beta_actual = float(beta_arr[bi])

    n_surfs = len(ctrl_surfaces)
    n_cols = min(n_surfs, 2)
    n_rows = (n_surfs + n_cols - 1) // n_cols

    for coef in COEF_NAMES:
        ctrl_keys = [f"{coef}_{s}" for s in ctrl_surfaces if f"{coef}_{s}" in aero.ctrl]
        if not ctrl_keys:
            continue

        fig_ctrl = make_subplots(
            rows=n_rows, cols=n_cols,
            specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
            subplot_titles=[aero.ctrl[k].surface for k in ctrl_keys],
            vertical_spacing=0.12,
            horizontal_spacing=0.01,
        )
        n_scenes = n_rows * n_cols
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_scenes)]
        for j, key in enumerate(ctrl_keys):
            ctrl_tbl = aero.ctrl[key]
            alpha_g, defl_g = np.meshgrid(ctrl_tbl.alpha, ctrl_tbl.defl, indexing="ij")
            fig_ctrl.add_trace(
                go.Surface(
                    x=alpha_g, y=defl_g, z=ctrl_tbl.data[:, bi, :],
                    colorscale=COLORSCALE_CTRL, opacity=OPACITY_SURFACE,
                    showscale=False, name=ctrl_tbl.surface,
                ),
                row=j // n_cols + 1, col=j % n_cols + 1,
            )
            fig_ctrl.update_layout(**{scene_names[j]: dict(
                aspectmode="cube",
                camera=CAMERA_AERO,
                xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                yaxis=dict(title=label_delta(ctrl_tbl.surface), **AXIS_3D),
                zaxis=dict(title=_COEF_LABEL[coef], **AXIS_3D),
            )})
        fig_ctrl.update_layout(
            title=dict(
                text=f"{coef}  (β = {beta_actual:.1f}°)",
                x=0.5, xanchor="center", y=0.99, yanchor="top",
            ),
            height=330 * n_rows,
            showlegend=False,
            margin=dict(l=30, r=30, t=55, b=20),
            modebar=dict(
                orientation="v",
                bgcolor="rgba(255,255,255,0.6)",
                color="#666",
                activecolor="#2563eb",
            ),
        )
        figs.append(fig_ctrl)

    return figs
