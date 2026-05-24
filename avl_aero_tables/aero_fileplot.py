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
    "beta": "β",
    "p": "p'",
    "q": "q'",
    "r": "r'",
}

# Single-letter subscript for each short-form coefficient prefix.
_COEF_SUBSCRIPT: dict[str, str] = {
    "CL": "L",
    "CY": "Y",
    "CD": "D",
    "Cl": "l",
    "Cm": "m",
    "Cn": "n",
}

# Human-readable word for each coefficient prefix (used in dict keys and filenames).
_COEF_WORD: dict[str, str] = {
    "CL": "lift",
    "CY": "side",
    "CD": "drag",
    "Cl": "roll",
    "Cm": "pitch",
    "Cn": "yaw",
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

# Perturbation-variable groupings for stability-derivative figures.
_DERIV_GROUPS: dict[str, tuple[str, ...]] = {
    "alpha": ("CLa", "CYa", "CDa", "Cla", "Cma", "Cna"),
    "beta": ("CLb", "CYb", "CDb", "Clb", "Cmb", "Cnb"),
    "p": ("CLp", "CYp", "CDp", "Clp", "Cmp", "Cnp"),
    "q": ("CLq", "CYq", "CDq", "Clq", "Cmq", "Cnq"),
    "r": ("CLr", "CYr", "CDr", "Clr", "Cmr", "Cnr"),
}

# Generated from _COEF_SUBSCRIPT × _PERTURB_UNICODE.
# e.g. "CLa" → "CLα",  "CLp" → "CLp'",  "Cnr" → "Cnr'"
_STAB_DERIV_LABEL: dict[str, str] = {
    f"{prefix}{var[0]}": f"C{sub}{unicode}"
    for prefix, sub in _COEF_SUBSCRIPT.items()
    for var, unicode in _PERTURB_UNICODE.items()
}

if TYPE_CHECKING:
    import plotly.graph_objects as go


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _init_figure(
    n_rows: int,
    n_cols: int,
    subplot_titles: list[str],
    title_text: str,
    height: int | None = None,
) -> "tuple[go.Figure, list[str]]":
    """Create a make_subplots figure with standard aero layout applied."""
    from plotly.subplots import make_subplots

    fig = make_subplots(
        rows=n_rows,
        cols=n_cols,
        specs=[[{"type": "scene"}] * n_cols for _ in range(n_rows)],
        subplot_titles=subplot_titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.01,
    )
    n_scenes = n_rows * n_cols
    scene_names = ["scene" if i == 0 else f"scene{i + 1}" for i in range(n_scenes)]
    fig.update_layout(
        title=dict(text=title_text, x=0.5, xanchor="center", y=0.99, yanchor="top"),
        height=(height or 330 * n_rows),
        showlegend=False,
        margin=dict(l=30, r=30, t=55, b=20),
        modebar=dict(
            orientation="v",
            bgcolor="rgba(255,255,255,0.6)",
            color="#666",
            activecolor="#2563eb",
        ),
    )
    return fig, scene_names


def _add_surface_trace(
    fig: "go.Figure",
    scene_names: list[str],
    i: int,
    n_cols: int,
    x: "np.ndarray",
    y: "np.ndarray",
    z: "np.ndarray",
    colorscale: str,
    x_label: str,
    y_label: str,
    z_label: str,
    name: str,
) -> None:
    """Add a go.Surface trace and scene layout update for subplot index i."""
    import plotly.graph_objects as go

    fig.add_trace(
        go.Surface(
            x=x,
            y=y,
            z=z,
            colorscale=colorscale,
            opacity=OPACITY_SURFACE,
            showscale=False,
            name=name,
        ),
        row=i // n_cols + 1,
        col=i % n_cols + 1,
    )
    fig.update_layout(
        **{
            scene_names[i]: dict(
                aspectmode="cube",
                camera=CAMERA_AERO,
                xaxis=dict(title=x_label, **AXIS_3D),
                yaxis=dict(title=y_label, **AXIS_3D),
                zaxis=dict(title=z_label, **AXIS_3D),
            )
        }
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def plot_totals(
    aero: AeroDatabase,
    beta_ref: float = 0.0,
) -> "dict[str, go.Figure]":
    """Plot stability and control coefficient tables from an AeroDatabase.

    Produces two sets of interactive figures:

    1. **Baseline aero figure** (key ``"stab"``) — grid of 3-D surface plots
       showing each of the six total-force coefficients (CLtot, CYtot, CDtot,
       Cltot, Cmtot, Cntot) vs. alpha and beta at neutral controls.

    2. **Control surface figures** (keys ``"ctrl_CL"`` … ``"ctrl_Cn"``) — one
       figure per coefficient, each containing one subplot per control surface.
       Shows how the total coefficient varies with alpha and deflection angle
       at *beta_ref*.  These are discrete coefficient values, not derivatives.

    Parameters
    ----------
    aero:
        AeroDatabase built by aero_filewrite().
    beta_ref:
        Sideslip angle (deg) at which control-surface subplots are sliced.
        The nearest available beta breakpoint is used.

    Returns
    -------
    dict[str, plotly.graph_objects.Figure]
        Keys: ``"stab"``, then ``"ctrl_lift"``, ``"ctrl_side"``, ``"ctrl_drag"``,
        ``"ctrl_roll"``, ``"ctrl_pitch"``, ``"ctrl_yaw"`` (control keys present
        only when ``aero.total_ctrl`` is non-empty).  Empty database returns ``{}``.
        Save with ``fig.write_html("out.html")``.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import plot_totals
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         ctrl_sweeps={"elevator": [-10, 0, 10]},
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = plot_totals(db)
    >>> len(figs)
    7
    >>> figs["stab"].layout.title.text
    'Aerodynamic Coefficients — Neutral Controls'
    >>> "_total" in figs["ctrl_lift"].layout.title.text
    True
    """
    figs: dict[str, go.Figure] = {}

    # ------------------------------------------------------------------
    # 1. Stability figure
    # ------------------------------------------------------------------
    stab_coefs = [c for c in COEF_NAMES if c in aero.total_stab]
    if stab_coefs:
        n_cols = 3
        n_rows = (len(stab_coefs) + n_cols - 1) // n_cols
        fig_stab, scene_names = _init_figure(
            n_rows,
            n_cols,
            [_COEF_LABEL.get(c, c) for c in stab_coefs],
            "Aerodynamic Coefficients — Neutral Controls",
        )
        for i, coef in enumerate(stab_coefs):
            tbl = aero.total_stab[coef]
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            _add_surface_trace(
                fig_stab,
                scene_names,
                i,
                n_cols,
                alpha_g,
                beta_g,
                tbl.data,
                COLORSCALE_STAB,
                LABEL_ALPHA,
                LABEL_BETA,
                _COEF_LABEL[coef],
                coef,
            )
        figs["stab"] = fig_stab

    # ------------------------------------------------------------------
    # 2. Control figures
    # ------------------------------------------------------------------
    ctrl_surfaces = list(dict.fromkeys(t.surface for t in aero.total_ctrl.values()))
    if not ctrl_surfaces:
        return figs

    sample_tbl = next(iter(aero.total_ctrl.values()))
    beta_arr = sample_tbl.beta
    bi = int(np.argmin(np.abs(beta_arr - beta_ref)))
    beta_actual = float(beta_arr[bi])

    n_surfs = len(ctrl_surfaces)
    n_cols_ctrl = min(n_surfs, 2)
    n_rows_ctrl = (n_surfs + n_cols_ctrl - 1) // n_cols_ctrl

    for coef in COEF_NAMES:
        ctrl_keys = [f"{coef}_{s}" for s in ctrl_surfaces if f"{coef}_{s}" in aero.total_ctrl]
        if not ctrl_keys:
            continue

        coef_short = coef[:-3]  # "CLtot" → "CL"
        fig_ctrl, scene_names = _init_figure(
            n_rows_ctrl,
            n_cols_ctrl,
            [aero.total_ctrl[k].surface for k in ctrl_keys],
            f"{_COEF_LABEL[coef]} vs. α, δ  (β = {beta_actual:.1f}°)",
        )
        for j, key in enumerate(ctrl_keys):
            ctrl_tbl = aero.total_ctrl[key]
            alpha_g, defl_g = np.meshgrid(ctrl_tbl.alpha, ctrl_tbl.defl, indexing="ij")
            _add_surface_trace(
                fig_ctrl,
                scene_names,
                j,
                n_cols_ctrl,
                alpha_g,
                defl_g,
                ctrl_tbl.data[:, bi, :],
                COLORSCALE_CTRL,
                LABEL_ALPHA,
                label_delta(ctrl_tbl.surface),
                _COEF_LABEL[coef],
                ctrl_tbl.surface,
            )
        figs[f"ctrl_{_COEF_WORD[coef_short]}"] = fig_ctrl

    return figs


def plot_stab_derivs(aero: AeroDatabase) -> "dict[str, go.Figure]":
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
    dict[str, plotly.graph_objects.Figure]
        Keys: ``"alpha"``, ``"beta"``, ``"p"``, ``"q"``, ``"r"`` — only groups
        whose derivatives are present in ``aero.stab_deriv`` are included.
        Empty database returns ``{}``.
        Save with ``fig.write_html("out.html")``.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import plot_stab_derivs
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = plot_stab_derivs(db)
    >>> len(figs)
    5
    >>> "Stability Derivatives" in figs["alpha"].layout.title.text
    True
    """
    figs: dict[str, go.Figure] = {}
    n_cols = 3
    n_rows = 2  # 6 subplots per figure in a 2×3 grid

    for perturb_var, keys in _DERIV_GROUPS.items():
        present = [k for k in keys if k in aero.stab_deriv]
        if not present:
            continue

        fig, scene_names = _init_figure(
            n_rows,
            n_cols,
            [_STAB_DERIV_LABEL.get(k, k) for k in keys],
            f"Stability Derivatives — ∂C*/∂{_PERTURB_UNICODE[perturb_var]}",
        )
        for i, key in enumerate(keys):
            if key not in aero.stab_deriv:
                continue
            tbl = aero.stab_deriv[key]
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            _add_surface_trace(
                fig,
                scene_names,
                i,
                n_cols,
                alpha_g,
                beta_g,
                tbl.data,
                COLORSCALE_STAB,
                LABEL_ALPHA,
                LABEL_BETA,
                _STAB_DERIV_LABEL.get(key, key),
                key,
            )
        figs[perturb_var] = fig

    return figs


def plot_ctrl_derivs(aero: AeroDatabase) -> "dict[str, go.Figure]":
    """Plot control-derivative tables from an AeroDatabase.

    Returns one figure per control surface.  Each figure contains six 3-D
    surface subplots — one per coefficient (CL, CY, CD, Cl, Cm, Cn) — showing
    how the linearised control derivative ∂C/∂δ_surface varies with alpha and
    beta.

    Parameters
    ----------
    aero:
        AeroDatabase built by aero_filewrite().

    Returns
    -------
    dict[str, plotly.graph_objects.Figure]
        Keys are control surface names (e.g. ``"flap"``, ``"elevator"``).
        Surfaces whose derivatives are all absent are skipped.
        Empty database returns ``{}``.
        Save with ``fig.write_html("out.html")``.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> from avl_aero_tables.aero_fileplot import plot_ctrl_derivs
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[-5, 0, 5],
    ...         out_dir=tmp,
    ...     )
    >>> db = aero_filewrite(results)
    >>> figs = plot_ctrl_derivs(db)
    >>> len(figs)
    4
    >>> "Control Derivatives" in figs["flap"].layout.title.text
    True
    >>> "flap" in figs["flap"].layout.title.text
    True
    """
    if not aero.ctrl_deriv:
        return {}

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

    figs: dict[str, go.Figure] = {}
    n_cols = 3
    n_rows = 2

    for surf_key, ctrl_name in surfaces:
        keys = [f"{coef}_{surf_key}" for coef in CTRL_DERIV_COEFS]
        present = [k for k in keys if k in aero.ctrl_deriv]
        if not present:
            continue

        subplot_titles = [
            f"{_CTRL_DERIV_SUBPLOT_LABEL.get(c, c)}_{ctrl_name}"
            for c in CTRL_DERIV_COEFS
        ]
        fig, scene_names = _init_figure(
            n_rows,
            n_cols,
            subplot_titles,
            f"Control Derivatives — ∂C*/∂δ_{ctrl_name}",
        )
        for i, key in enumerate(keys):
            if key not in aero.ctrl_deriv:
                continue
            tbl = aero.ctrl_deriv[key]
            c = CTRL_DERIV_COEFS[i]
            sub = _COEF_SUBSCRIPT.get(c, c)
            alpha_g, beta_g = np.meshgrid(tbl.alpha, tbl.beta, indexing="ij")
            _add_surface_trace(
                fig,
                scene_names,
                i,
                n_cols,
                alpha_g,
                beta_g,
                tbl.data,
                COLORSCALE_CTRL,
                LABEL_ALPHA,
                LABEL_BETA,
                f"C{sub}δ_{ctrl_name}",
                key,
            )
        figs[ctrl_name] = fig

    return figs
