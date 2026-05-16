"""Plot AeroDatabase tables as interactive 3-D plotly surface figures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import numpy as np

from avl_aero_tables.aero_filewrite import COEF_NAMES, AeroDatabase

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
    >>> with tempfile.TemporaryDirectory() as tmp:  # doctest: +ELLIPSIS
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         ctrl_sweeps={"elevator": [-10, 0, 10]},
    ...         out_dir=tmp,
    ...     )
    AVL sweep complete → ...  (36 cases)
    >>> db = aero_filewrite(results)
    >>> figs = aero_fileplot(db)
    >>> len(figs)
    7
    >>> figs[0].layout.title.text
    'Stability coefficients'
    >>> figs[1].layout.title.text
    'CLtot  —  beta = 0.0 deg'
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
            subplot_titles=stab_coefs,
        )
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_rows * n_cols)]
        for i, coef in enumerate(stab_coefs):
            tbl = aero.stab[coef]
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            fig_stab.add_trace(
                go.Surface(x=alpha_g, y=beta_g, z=tbl.data, colorscale="Viridis", opacity=0.9, showscale=False, name=coef),
                row=i // n_cols + 1, col=i % n_cols + 1,
            )
            fig_stab.update_layout(**{scene_names[i]: dict(
                aspectmode="cube",
                xaxis=dict(title="Alpha (deg)"),
                yaxis=dict(title="Beta (deg)"),
                zaxis=dict(title=coef),
            )})
        fig_stab.update_layout(title_text="Stability coefficients", height=400 * n_rows, showlegend=False)
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
        )
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_rows * n_cols)]
        for j, key in enumerate(ctrl_keys):
            tbl = aero.ctrl[key]
            alpha_g, defl_g = np.meshgrid(tbl.alpha, tbl.defl, indexing="ij")
            fig_ctrl.add_trace(
                go.Surface(x=alpha_g, y=defl_g, z=tbl.data[:, bi, :], colorscale="Plasma", opacity=0.9, showscale=False, name=tbl.surface),
                row=j // n_cols + 1, col=j % n_cols + 1,
            )
            fig_ctrl.update_layout(**{scene_names[j]: dict(
                aspectmode="cube",
                xaxis=dict(title="Alpha (deg)"),
                yaxis=dict(title=f"{tbl.ctrl_name} (deg)"),
                zaxis=dict(title=coef),
            )})
        fig_ctrl.update_layout(
            title_text=f"{coef}  —  beta = {beta_actual:.1f} deg",
            height=400 * n_rows,
            showlegend=False,
        )
        figs.append(fig_ctrl)

    return figs
