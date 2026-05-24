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
from avl_aero_tables.aero_filewrite import (
    COEF_NAMES,
    CTRL_DERIV_COEFS,
    AeroDatabase,
)

# Display labels for each total coefficient (standard aerospace notation)
_COEF_LABEL: dict[str, str] = {
    "CLtot": "CL_total",
    "CYtot": "CY_total",
    "CDtot": "CD_total",
    "Cltot": "Cl_total",
    "Cmtot": "Cm_total",
    "Cntot": "Cn_total",
}

# Maps plain perturbation identifier → Unicode string used in axis labels and titles.
_PERTURB_UNICODE: dict[str, str] = {
    "alpha": "α",
    "beta":  "β",
    "p":     "p'",
    "q":     "q'",
    "r":     "r'",
}

# Single-letter subscript for each short-form coefficient (used to build LaTeX labels).
_COEF_SUBSCRIPT: dict[str, str] = {
    "CL": "L", "CY": "Y", "CD": "D", "Cl": "l", "Cm": "m", "Cn": "n",
}

# Subplot titles for control-derivative figures: generic δ (surface is in figure title).
_CTRL_DERIV_SUBPLOT_LABEL: dict[str, str] = {
    "CL": "CLδ",
    "CY": "CYδ",
    "CD": "CDδ",
    "Cl": "Clδ",
    "Cm": "Cmδ",
    "Cn": "Cnδ",
}

if TYPE_CHECKING:
    import plotly.graph_objects as go


def aero_fileplot(
    aero: AeroDatabase,
    beta_ref: float = 0.0,
) -> "list[go.Figure]":
    """Plot stability and control coefficient tables from an AeroDatabase.

    Produces two sets of interactive figures:

    1. **Baseline aero figure** — grid of 3-D surface plots showing each of
       the six total-force coefficients (CLtot, CYtot, CDtot, Cltot, Cmtot,
       Cntot) vs. alpha and beta at neutral controls (all surfaces at 0°).

    2. **Control surface figures** — one figure per coefficient, each
       containing one subplot per control surface. Shows how the total
       coefficient varies with alpha and deflection angle at *beta_ref*.
       These are discrete coefficient values, not linearised derivatives.

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
    'Aerodynamic Coefficients — Neutral Controls'
    >>> "_total" in figs[1].layout.title.text
    True
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
            rows=n_rows,
            cols=n_cols,
            specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
            subplot_titles=[_COEF_LABEL.get(c, c) for c in stab_coefs],
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
                    x=alpha_g,
                    y=beta_g,
                    z=tbl.data,
                    colorscale=COLORSCALE_STAB,
                    opacity=OPACITY_SURFACE,
                    showscale=False,
                    name=coef,
                ),
                row=i // n_cols + 1,
                col=i % n_cols + 1,
            )
            fig_stab.update_layout(
                **{
                    scene_names[i]: dict(
                        aspectmode="cube",
                        camera=CAMERA_AERO,
                        xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                        yaxis=dict(title=LABEL_BETA, **AXIS_3D),
                        zaxis=dict(title=_COEF_LABEL[coef], **AXIS_3D),
                    )
                }
            )
        fig_stab.update_layout(
            title=dict(
                text="Aerodynamic Coefficients — Neutral Controls",
                x=0.5,
                xanchor="center",
                y=0.99,
                yanchor="top",
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
            rows=n_rows,
            cols=n_cols,
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
                    x=alpha_g,
                    y=defl_g,
                    z=ctrl_tbl.data[:, bi, :],
                    colorscale=COLORSCALE_CTRL,
                    opacity=OPACITY_SURFACE,
                    showscale=False,
                    name=ctrl_tbl.surface,
                ),
                row=j // n_cols + 1,
                col=j % n_cols + 1,
            )
            fig_ctrl.update_layout(
                **{
                    scene_names[j]: dict(
                        aspectmode="cube",
                        camera=CAMERA_AERO,
                        xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                        yaxis=dict(title=label_delta(ctrl_tbl.surface), **AXIS_3D),
                        zaxis=dict(title=_COEF_LABEL[coef], **AXIS_3D),
                    )
                }
            )
        fig_ctrl.update_layout(
            title=dict(
                text=f"{_COEF_LABEL[coef]} vs. α, δ  (β = {beta_actual:.1f}°)",
                x=0.5,
                xanchor="center",
                y=0.99,
                yanchor="top",
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


# Perturbation-variable groupings for stability-derivative figures.
# Keys are plain identifiers; use _PERTURB_LATEX for display strings.
_DERIV_GROUPS: dict[str, tuple[str, ...]] = {
    "alpha": ("CLa", "CYa", "CDa", "Cla", "Cma", "Cna"),
    "beta":  ("CLb", "CYb", "CDb", "Clb", "Cmb", "Cnb"),
    "p":     ("CLp", "CYp", "CDp", "Clp", "Cmp", "Cnp"),
    "q":     ("CLq", "CYq", "CDq", "Clq", "Cmq", "Cnq"),
    "r":     ("CLr", "CYr", "CDr", "Clr", "Cmr", "Cnr"),
}

_STAB_DERIV_LABEL: dict[str, str] = {
    "CLa": "CLα",  "CYa": "CYα",
    "CDa": "CDα",  "Cla": "Clα",
    "Cma": "Cmα",  "Cna": "Cnα",
    "CLb": "CLβ",  "CYb": "CYβ",
    "CDb": "CDβ",  "Clb": "Clβ",
    "Cmb": "Cmβ",  "Cnb": "Cnβ",
    "CLp": "CLp'", "CYp": "CYp'",
    "CDp": "CDp'", "Clp": "Clp'",
    "Cmp": "Cmp'", "Cnp": "Cnp'",
    "CLq": "CLq'", "CYq": "CYq'",
    "CDq": "CDq'", "Clq": "Clq'",
    "Cmq": "Cmq'", "Cnq": "Cnq'",
    "CLr": "CLr'", "CYr": "CYr'",
    "CDr": "CDr'", "Clr": "Clr'",
    "Cmr": "Cmr'", "Cnr": "Cnr'",
}


def aero_stabderivplot(aero: AeroDatabase) -> "list[go.Figure]":
    """Plot stability-axis derivative tables from an AeroDatabase.

    Returns one figure per perturbation variable (α, β, p', q', r').  Each
    figure contains six 3-D surface subplots — one per force/moment coefficient
    (CL, CY, CD, Cl, Cm, Cn) — showing how the linearised derivative varies
    with alpha and beta at neutral controls.

    Parameters
    ----------
    aero:
        AeroDatabase built by aero_filewrite().

    Returns
    -------
    list[plotly.graph_objects.Figure]
        Up to five figures; any group whose derivatives are all absent from
        ``aero.stab_deriv`` is skipped.
        Save with ``fig.write_html("out.html")``.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import aero_stabderivplot
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = aero_stabderivplot(db)
    >>> len(figs)
    5
    >>> "Stability Derivatives" in figs[0].layout.title.text
    True
    >>> "alpha" in figs[0].layout.title.text
    True
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    figs: list[go.Figure] = []
    n_cols = 3
    n_rows = 2  # 6 subplots per figure in a 2×3 grid

    for perturb_var, keys in _DERIV_GROUPS.items():
        present = [k for k in keys if k in aero.stab_deriv]
        if not present:
            continue

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
            subplot_titles=[_STAB_DERIV_LABEL.get(k, k) for k in keys],
            vertical_spacing=0.12,
            horizontal_spacing=0.01,
        )
        n_scenes = n_rows * n_cols
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_scenes)]

        for i, key in enumerate(keys):
            if key not in aero.stab_deriv:
                continue
            tbl = aero.stab_deriv[key]
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            fig.add_trace(
                go.Surface(
                    x=alpha_g,
                    y=beta_g,
                    z=tbl.data,
                    colorscale=COLORSCALE_STAB,
                    opacity=OPACITY_SURFACE,
                    showscale=False,
                    name=key,
                ),
                row=i // n_cols + 1,
                col=i % n_cols + 1,
            )
            fig.update_layout(
                **{
                    scene_names[i]: dict(
                        aspectmode="cube",
                        camera=CAMERA_AERO,
                        xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                        yaxis=dict(title=LABEL_BETA, **AXIS_3D),
                        zaxis=dict(title=_STAB_DERIV_LABEL.get(key, key), **AXIS_3D),
                    )
                }
            )

        fig.update_layout(
            title=dict(
                text=f"Stability Derivatives — ∂C*/∂{_PERTURB_UNICODE[perturb_var]}",
                x=0.5,
                xanchor="center",
                y=0.99,
                yanchor="top",
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
        figs.append(fig)

    return figs


def aero_ctrlderivplot(aero: AeroDatabase) -> "list[go.Figure]":
    """Plot control-derivative tables from an AeroDatabase.

    Returns one figure per control surface.  Each figure contains six 3-D
    surface subplots — one per coefficient ($C_L$, $C_Y$, $C_D$, $C_l$,
    $C_m$, $C_n$) — showing how the linearised control derivative
    $\\partial C / \\partial \\delta_{\\text{surface}}$ varies with alpha and beta.

    Parameters
    ----------
    aero:
        AeroDatabase built by aero_filewrite().

    Returns
    -------
    list[plotly.graph_objects.Figure]
        One figure per surface present in ``aero.ctrl_deriv``; surfaces whose
        derivatives are all absent are skipped.
        Save with ``fig.write_html("out.html")``.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import aero_ctrlderivplot
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = aero_ctrlderivplot(db)
    >>> len(figs)
    4
    >>> "Control Derivatives" in figs[0].layout.title.text
    True
    >>> "flap" in figs[0].layout.title.text
    True
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

    if not aero.ctrl_deriv:
        return []

    # Collect unique surfaces preserving insertion order
    surfaces: list[tuple[str, str]] = []  # [(surf_key, ctrl_name), …]
    seen: set[str] = set()
    for key in aero.ctrl_deriv:
        # key format: "{coef}_{d_idx}_{ctrl_name}", e.g. "CL_d01_flap"
        parts = key.split("_", 1)  # ["CL", "d01_flap"]
        surf = parts[1] if len(parts) == 2 else key
        if surf not in seen:
            seen.add(surf)
            ctrl_name = "_".join(surf.split("_")[1:])  # "flap" from "d01_flap"
            surfaces.append((surf, ctrl_name))

    figs: list[go.Figure] = []
    n_cols = 3
    n_rows = 2

    for surf_key, ctrl_name in surfaces:
        keys = [f"{coef}_{surf_key}" for coef in CTRL_DERIV_COEFS]
        present = [k for k in keys if k in aero.ctrl_deriv]
        if not present:
            continue

        fig = make_subplots(
            rows=n_rows,
            cols=n_cols,
            specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
            subplot_titles=[f"{_CTRL_DERIV_SUBPLOT_LABEL.get(c, c)}_{ctrl_name}" for c in CTRL_DERIV_COEFS],
            vertical_spacing=0.12,
            horizontal_spacing=0.01,
        )
        n_scenes = n_rows * n_cols
        scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_scenes)]

        for i, key in enumerate(keys):
            if key not in aero.ctrl_deriv:
                continue
            tbl = aero.ctrl_deriv[key]
            c = CTRL_DERIV_COEFS[i]
            sub = _COEF_SUBSCRIPT.get(c, c)
            z_label = f"C{sub}δ_{ctrl_name}"
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            fig.add_trace(
                go.Surface(
                    x=alpha_g,
                    y=beta_g,
                    z=tbl.data,
                    colorscale=COLORSCALE_CTRL,
                    opacity=OPACITY_SURFACE,
                    showscale=False,
                    name=key,
                ),
                row=i // n_cols + 1,
                col=i % n_cols + 1,
            )
            fig.update_layout(
                **{
                    scene_names[i]: dict(
                        aspectmode="cube",
                        camera=CAMERA_AERO,
                        xaxis=dict(title=LABEL_ALPHA, **AXIS_3D),
                        yaxis=dict(title=LABEL_BETA, **AXIS_3D),
                        zaxis=dict(title=z_label, **AXIS_3D),
                    )
                }
            )

        fig.update_layout(
            title=dict(
                text=f"Control Derivatives — ∂C*/∂δ_{ctrl_name}",
                x=0.5,
                xanchor="center",
                y=0.99,
                yanchor="top",
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
        figs.append(fig)

    return figs
