"""Plot AeroDatabase tables as 3-D surface plots (port of aero_fileplot.m)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from avl_wrapper.aero_filewrite import COEF_NAMES, AeroDatabase

if TYPE_CHECKING:
    import matplotlib.pyplot as plt


def aero_fileplot(
    aero: AeroDatabase,
    beta_ref: float = 0.0,
) -> list[plt.Figure]:
    """Plot stability and control coefficient tables from an AeroDatabase.

    Produces two sets of figures:

    1. **Stability figure** — 2×3 grid of 3-D surface plots showing each of
       the six total-force coefficients vs. alpha and beta.

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
    list[plt.Figure]
        Stability figure first, then one control figure per coefficient.
        Returns an empty list for any set that cannot be plotted (e.g. no
        control surfaces).

    Example
    -------
    >>> from avl_wrapper import avl_sweep
    >>> from avl_wrapper.aero_filewrite import aero_filewrite
    >>> from avl_wrapper.aero_fileplot import aero_fileplot
    >>> results = avl_sweep.run("examples/bd.avl", alpha=[-5, 0, 5, 10], beta=[0])
    >>> db = aero_filewrite(results)
    >>> figs = aero_fileplot(db)
    >>> figs[0].get_suptitle()
    'Stability coefficients'
    >>> figs[0].savefig("stability.png")
    """
    import matplotlib.pyplot as plt

    figs: list[plt.Figure] = []

    # ------------------------------------------------------------------
    # 1. Stability figure (alpha × beta for each coefficient)
    # ------------------------------------------------------------------
    stab_coefs = [c for c in COEF_NAMES if c in aero.stab]
    if stab_coefs:
        n_cols = 3
        n_rows = (len(stab_coefs) + n_cols - 1) // n_cols
        fig_stab = plt.figure(figsize=(14, 4 * n_rows))
        fig_stab.suptitle("Stability coefficients")

        for i, coef in enumerate(stab_coefs, start=1):
            stab_tbl = aero.stab[coef]
            ax = fig_stab.add_subplot(n_rows, n_cols, i, projection="3d")
            alpha_g, beta_g = np.meshgrid(stab_tbl.alpha, stab_tbl.beta, indexing="ij")  # type: ignore[call-overload]
            ax.plot_surface(alpha_g, beta_g, stab_tbl.data, cmap="viridis", alpha=0.85)
            ax.set_xlabel("Alpha (deg)")
            ax.set_ylabel("Beta (deg)")
            ax.set_zlabel(coef)
            ax.set_title(coef)
            ax.view_init(elev=30, azim=-37.5)

        fig_stab.tight_layout()
        figs.append(fig_stab)

    # ------------------------------------------------------------------
    # 2. Control figures (alpha × deflection at beta_ref)
    # ------------------------------------------------------------------
    ctrl_surfaces = list(dict.fromkeys(t.surface for t in aero.ctrl.values()))

    if not ctrl_surfaces:
        return figs

    # Find the beta index nearest to beta_ref
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

        fig_ctrl = plt.figure(figsize=(6 * n_cols, 4 * n_rows))
        fig_ctrl.suptitle(f"{coef}  —  beta = {beta_actual:.1f} deg")

        for j, key in enumerate(ctrl_keys, start=1):
            ctrl_tbl = aero.ctrl[key]
            ax = fig_ctrl.add_subplot(n_rows, n_cols, j, projection="3d")
            alpha_g, defl_g = np.meshgrid(ctrl_tbl.alpha, ctrl_tbl.defl, indexing="ij")  # type: ignore[call-overload]
            z = ctrl_tbl.data[:, bi, :]
            ax.plot_surface(alpha_g, defl_g, z, cmap="plasma", alpha=0.85)
            ax.set_xlabel("Alpha (deg)")
            ax.set_ylabel(f"{ctrl_tbl.ctrl_name} (deg)")
            ax.set_zlabel(coef)
            ax.set_title(ctrl_tbl.surface)
            ax.view_init(elev=30, azim=-37.5)

        fig_ctrl.tight_layout()
        figs.append(fig_ctrl)

    return figs
