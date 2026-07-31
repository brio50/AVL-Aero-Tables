"""Convert list[StResult] into structured aero lookup tables."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date as _date
from typing import TYPE_CHECKING, Any

import numpy as np

from avl_aero_tables.avl_fileread import StResult

if TYPE_CHECKING:
    import pandas as pd

COEF_NAMES = ("CLtot", "CYtot", "CDtot", "Cltot", "Cmtot", "Cntot")
REF_FIELDS = ("Sref", "Cref", "Bref", "Xref", "Yref", "Zref")

# Stability-axis derivatives — keys exactly as written in AVL .st files
STAB_DERIV_ALPHA_BETA = (
    "CLa",
    "CLb",
    "CYa",
    "CYb",
    "CDa",
    "CDb",
    "Cla",
    "Clb",
    "Cma",
    "Cmb",
    "Cna",
    "Cnb",
)
STAB_DERIV_RATES = (
    "CLp",
    "CLq",
    "CLr",
    "CYp",
    "CYq",
    "CYr",
    "CDp",
    "CDq",
    "CDr",
    "Clp",
    "Clq",
    "Clr",
    "Cmp",
    "Cmq",
    "Cmr",
    "Cnp",
    "Cnq",
    "Cnr",
)
STAB_DERIV_NAMES = STAB_DERIV_ALPHA_BETA + STAB_DERIV_RATES  # 30 total

# Control-derivative prefixes — AVL writes CLd01, CYd01, CDd01, Cld01, Cmd01, Cnd01
# (no "tot" suffix — these are linearised ∂coef/∂δ, not integrated totals)
CTRL_DERIV_COEFS = ("CL", "CY", "CD", "Cl", "Cm", "Cn")


@dataclass
class StabTable:
    """2-D coefficient lookup table indexed by (alpha, beta).

    Populated only for runs where all control surfaces are at neutral (0 deg).
    """

    coef: str
    alpha: np.ndarray  # shape (n_alpha,), sorted unique
    beta: np.ndarray  # shape (n_beta,),  sorted unique
    data: np.ndarray  # shape (n_alpha, n_beta), NaN where unfilled


@dataclass
class CtrlTable:
    """3-D coefficient lookup table indexed by (alpha, beta, deflection)."""

    coef: str
    surface: str  # e.g. "d01_flap"
    ctrl_name: str  # e.g. "flap"
    alpha: np.ndarray
    beta: np.ndarray
    defl: np.ndarray  # shape (n_defl,), sorted unique deflections
    data: np.ndarray  # shape (n_alpha, n_beta, n_defl), NaN where unfilled


@dataclass
class AeroDatabase:
    """Aero coefficient tables built from a sweep of AVL .st results.

    total_stab[coef]     → StabTable  total coefficients, neutral-control, indexed α×β
    total_ctrl[coef_surface] → CtrlTable  total coefficients, all deflections, indexed α×β×δ
    stab_deriv[key]      → StabTable  stability derivatives (CLa, CLb, CLp, …, Cnr), neutral-control only, indexed α×β
    ctrl_deriv[key]      → StabTable  control derivatives (CL_d01_flap, …), neutral-control only, indexed α×β
    """

    date: str
    Sref: float = 0.0
    Cref: float = 0.0
    Bref: float = 0.0
    Xref: float = 0.0
    Yref: float = 0.0
    Zref: float = 0.0
    total_stab: dict[str, StabTable] = field(default_factory=dict)
    total_ctrl: dict[str, CtrlTable] = field(default_factory=dict)
    stab_deriv: dict[str, StabTable] = field(default_factory=dict)
    ctrl_deriv: dict[str, StabTable] = field(default_factory=dict)
    _interp_cache: dict[tuple[Any, ...], Callable[[np.ndarray], np.ndarray]] = field(
        default_factory=dict, repr=False, compare=False
    )

    def interpolate(
        self,
        coef: str,
        alpha: float | np.ndarray,
        beta: float | np.ndarray,
        defl: float | np.ndarray = 0.0,
        surface: str | None = None,
        method: str = "linear",
        bounds_error: bool = True,
    ) -> float | np.ndarray:
        """Interpolate a coefficient at an arbitrary (alpha, beta[, defl]) point.

        Looks up ``total_stab[coef]`` (2-D, neutral-control) when ``surface`` is
        omitted, or ``total_ctrl[f"{coef}_{surface}"]`` (3-D, indexed by
        deflection too) when ``surface`` is given. ``alpha``/``beta``/``defl``
        may be scalars or broadcastable arrays for batch queries (e.g. an
        entire flight trajectory at once).

        Parameters
        ----------
        coef:
            Coefficient name, e.g. "CLtot" (see COEF_NAMES).
        alpha, beta:
            Query point(s), in the same units as the breakpoints (degrees).
        defl:
            Control surface deflection(s) (degrees). Must be 0.0 unless
            ``surface`` is given — a neutral (`total_stab`) table has no
            deflection axis to interpolate against.
        surface:
            Control surface key, e.g. "d01_flap" (`CtrlTable.surface`).
            Required to interpolate at a non-zero deflection.
        method:
            Passed to `scipy.interpolate.RegularGridInterpolator`. "linear"
            (default) works for any breakpoint count; "pchip"/"cubic" need
            at least 4 breakpoints along every non-degenerate axis.
        bounds_error:
            Raise if the query point falls outside the swept range (default).
            Extrapolating an AVL table beyond its swept envelope — e.g. past
            stall — is not physically justified, so this defaults to strict.

        Returns
        -------
        float | np.ndarray
            A scalar if alpha, beta, and defl were all scalars; otherwise an
            array broadcast to their common shape.

        Example
        -------
        >>> import tempfile
        >>> from avl_aero_tables import avl_sweep
        >>> with tempfile.TemporaryDirectory() as tmp:
        ...     results = avl_sweep(
        ...         "examples/bd/bd.avl", alpha=[-5, 0, 5, 10], beta=[0], out_dir=tmp
        ...     )
        >>> db = aero_filewrite(results)
        >>> round(db.interpolate("CLtot", alpha=2.5, beta=0.0), 4) > 0
        True
        """
        alpha_arr = np.asarray(alpha, dtype=float)
        beta_arr = np.asarray(beta, dtype=float)
        defl_arr = np.asarray(defl, dtype=float)
        scalar_query = alpha_arr.ndim == 0 and beta_arr.ndim == 0 and defl_arr.ndim == 0

        if surface is not None:
            key = f"{coef}_{surface}"
            if key not in self.total_ctrl:
                available = sorted(
                    s.surface for s in self.total_ctrl.values() if s.coef == coef
                )
                raise KeyError(
                    f"{key!r} not found in total_ctrl — available surfaces for "
                    f"{coef!r}: {available}"
                )
            table_ctrl = self.total_ctrl[key]
            axes: tuple[np.ndarray, ...] = (
                table_ctrl.alpha,
                table_ctrl.beta,
                table_ctrl.defl,
            )
            data = table_ctrl.data
            alpha_b, beta_b, defl_b = np.broadcast_arrays(alpha_arr, beta_arr, defl_arr)
            pts = np.stack([alpha_b, beta_b, defl_b], axis=-1)
            cache_key: tuple[Any, ...] = ("ctrl", key, method, bounds_error)
        else:
            if np.any(defl_arr != 0.0):
                raise ValueError(
                    "defl must be 0.0 when surface is not specified — total_stab "
                    "has no deflection axis; pass surface=<name> to interpolate "
                    "a total_ctrl table at a non-zero deflection"
                )
            if coef not in self.total_stab:
                raise KeyError(
                    f"{coef!r} not found in total_stab — available: "
                    f"{sorted(self.total_stab)}"
                )
            table_stab = self.total_stab[coef]
            axes = (table_stab.alpha, table_stab.beta)
            data = table_stab.data
            alpha_b, beta_b = np.broadcast_arrays(alpha_arr, beta_arr)
            pts = np.stack([alpha_b, beta_b], axis=-1)
            cache_key = ("stab", coef, method, bounds_error)

        cached = self._interp_cache.get(cache_key)
        if cached is None:
            keep = [i for i, ax in enumerate(axes) if ax.size > 1]
            interp_fn: Callable[[np.ndarray], np.ndarray]
            if not keep:
                value = float(np.asarray(data).reshape(-1)[0])

                def interp_fn(query_pts: np.ndarray) -> np.ndarray:
                    return np.full(query_pts.shape[:-1], value)

            else:
                from scipy.interpolate import RegularGridInterpolator

                squeeze_axes = tuple(i for i in range(len(axes)) if i not in keep)
                grid_interp = RegularGridInterpolator(
                    tuple(axes[i] for i in keep),
                    np.squeeze(data, axis=squeeze_axes) if squeeze_axes else data,
                    method=method,
                    bounds_error=bounds_error,
                )
                if len(keep) == len(axes):
                    interp_fn = grid_interp
                else:

                    def interp_fn(query_pts: np.ndarray) -> np.ndarray:
                        return np.asarray(grid_interp(query_pts[..., keep]))

            cached = interp_fn
            self._interp_cache[cache_key] = cached

        result = cached(pts)
        return result.item() if scalar_query else result


def _sorted_unique(vals: list[float]) -> np.ndarray:
    return np.array(sorted({round(v, 8) for v in vals}))


def _find_idx(arr: np.ndarray, val: float, atol: float = 1e-6) -> int:
    i = int(np.searchsorted(arr, val))
    if i < len(arr) and abs(arr[i] - val) <= atol:
        return i
    if i > 0 and abs(arr[i - 1] - val) <= atol:
        return i - 1
    raise ValueError(f"{val!r} not in breakpoints {arr}")


def aero_filewrite(results: list[StResult]) -> AeroDatabase:
    """Pivot list[StResult] into an AeroDatabase of (alpha × beta [× defl]) tables.

    Stability tables are populated only for neutral-control runs (all deflections
    zero).  Control tables are populated for all runs regardless of deflection.

    Parameters
    ----------
    results:
        Output from avl_sweep.run() or st_fileread().

    Returns
    -------
    AeroDatabase
        Structured lookup tables keyed by coefficient name (and surface name
        for control tables).

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import aero_filewrite
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl", alpha=[-5, 0, 5, 10], beta=[0], out_dir=tmp
    ...     )
    >>> db = aero_filewrite(results)
    >>> db.total_stab["CLtot"].data.shape
    (4, 1)
    >>> list(db.total_stab)
    ['CLtot', 'CYtot', 'CDtot', 'Cltot', 'Cmtot', 'Cntot']
    """
    if not results:
        raise ValueError("results is empty")

    r0 = results[0]
    for r in results:
        for key in ("Alpha", "Beta"):
            if key not in r.data:
                raise ValueError(
                    f"StResult from {r.filename!r} is missing {key!r} — "
                    "was the .st file parsed correctly?"
                )
    alpha_arr = _sorted_unique([r.data["Alpha"] for r in results])
    beta_arr = _sorted_unique([r.data["Beta"] for r in results])

    ctrl_map: dict[str, str] = dict(r0.controls)  # {d01: flap, d02: aileron, …}

    surface_defls: dict[str, np.ndarray] = {
        d_idx: _sorted_unique([r.data.get(ctrl_name, 0.0) for r in results])
        for d_idx, ctrl_name in ctrl_map.items()
    }

    db = AeroDatabase(date=str(_date.today()))
    for fld in REF_FIELDS:
        if fld in r0.data:
            setattr(db, fld, r0.data[fld])

    for coef in COEF_NAMES:
        db.total_stab[coef] = StabTable(
            coef=coef,
            alpha=alpha_arr,
            beta=beta_arr,
            data=np.full((len(alpha_arr), len(beta_arr)), np.nan),
        )

    for d_idx, ctrl_name in ctrl_map.items():
        surf_key = f"{d_idx}_{ctrl_name}"
        defl_arr = surface_defls[d_idx]
        for coef in COEF_NAMES:
            db.total_ctrl[f"{coef}_{surf_key}"] = CtrlTable(
                coef=coef,
                surface=surf_key,
                ctrl_name=ctrl_name,
                alpha=alpha_arr,
                beta=beta_arr,
                defl=defl_arr,
                data=np.full((len(alpha_arr), len(beta_arr), len(defl_arr)), np.nan),
            )

    for key in STAB_DERIV_NAMES:
        db.stab_deriv[key] = StabTable(
            coef=key,
            alpha=alpha_arr,
            beta=beta_arr,
            data=np.full((len(alpha_arr), len(beta_arr)), np.nan),
        )

    for d_idx, ctrl_name in ctrl_map.items():
        for coef in CTRL_DERIV_COEFS:
            avl_key = f"{coef}{d_idx}"  # "CLd01" — key in StResult.data
            db_key = f"{coef}_{d_idx}_{ctrl_name}"  # "CL_d01_flap" — dict key
            db.ctrl_deriv[db_key] = StabTable(
                coef=avl_key,
                alpha=alpha_arr,
                beta=beta_arr,
                data=np.full((len(alpha_arr), len(beta_arr)), np.nan),
            )

    for r in results:
        ai = _find_idx(alpha_arr, r.data["Alpha"])
        bi = _find_idx(beta_arr, r.data["Beta"])
        all_neutral = all(
            abs(r.data.get(name, 0.0)) < 1e-6 for name in ctrl_map.values()
        )

        for coef in COEF_NAMES:
            val = r.data.get(coef, np.nan)
            if all_neutral:
                db.total_stab[coef].data[ai, bi] = val
            for d_idx, ctrl_name in ctrl_map.items():
                surf_key = f"{d_idx}_{ctrl_name}"
                defl_val = r.data.get(ctrl_name, 0.0)
                di = _find_idx(surface_defls[d_idx], defl_val)
                db.total_ctrl[f"{coef}_{surf_key}"].data[ai, bi, di] = val

        if all_neutral:
            for key in STAB_DERIV_NAMES:
                db.stab_deriv[key].data[ai, bi] = r.data.get(key, np.nan)
            for d_idx, ctrl_name in ctrl_map.items():
                for coef in CTRL_DERIV_COEFS:
                    avl_key = f"{coef}{d_idx}"
                    db_key = f"{coef}_{d_idx}_{ctrl_name}"
                    db.ctrl_deriv[db_key].data[ai, bi] = r.data.get(avl_key, np.nan)

    return db


def _is_neutral(r: StResult) -> bool:
    return all(abs(r.data.get(name, 0.0)) < 1e-6 for name in r.controls.values())


def stab_deriv_to_dataframe(results: list[StResult]) -> "pd.DataFrame":
    """Return a DataFrame of stability derivatives for neutral-control cases only.

    Columns: filename, Alpha, Beta, CLa, CLb, …, Cnr (30 derivative columns).
    One row per neutral-control (α, β) point.
    """
    import pandas as pd

    rows = []
    for r in results:
        if not _is_neutral(r):
            continue
        row: dict[str, object] = {
            "filename": r.filename,
            "Alpha": r.data.get("Alpha"),
            "Beta": r.data.get("Beta"),
        }
        for key in STAB_DERIV_NAMES:
            row[key] = r.data.get(key, float("nan"))
        rows.append(row)
    return pd.DataFrame(rows)


def ctrl_deriv_to_dataframe(results: list[StResult]) -> "pd.DataFrame":
    """Return a DataFrame of control derivatives for neutral-control cases only.

    Columns: filename, Alpha, Beta, CLd01, CYd01, …, Cnd{n} (6 × n_surfaces columns).
    One row per neutral-control (α, β) point.
    AVL notation: CLd01 = ∂CL/∂δ_surface1, no "tot" suffix.
    """
    import pandas as pd

    ctrl_map = dict(results[0].controls) if results else {}
    rows = []
    for r in results:
        if not _is_neutral(r):
            continue
        row: dict[str, object] = {
            "filename": r.filename,
            "Alpha": r.data.get("Alpha"),
            "Beta": r.data.get("Beta"),
        }
        for d_idx in ctrl_map:
            for coef in CTRL_DERIV_COEFS:
                avl_key = f"{coef}{d_idx}"  # e.g. "CLd01"
                row[avl_key] = r.data.get(avl_key, float("nan"))
        rows.append(row)
    return pd.DataFrame(rows)


def results_to_dataframe(results: list[StResult]) -> "pd.DataFrame":
    """Convert a list of StResult to a pandas DataFrame (one row per case).

    Each row contains the filename plus every key from StResult.data
    (Alpha, Beta, CLtot, control deflections, stability derivatives, etc.).
    This is the recommended format for saving results to CSV, HDF5, Parquet,
    or any other tabular format.

    Example
    -------
    >>> import tempfile
    >>> from avl_aero_tables import avl_sweep
    >>> from avl_aero_tables.aero_filewrite import results_to_dataframe
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(
    ...         "examples/bd/bd.avl", alpha=[0, 5], beta=[0], out_dir=tmp
    ...     )
    >>> df = results_to_dataframe(results)
    >>> "Alpha" in df.columns and "CLtot" in df.columns
    True
    >>> df.to_csv("tests/sweep.csv", index=False)
    """
    import pandas as pd

    rows = [{"filename": r.filename, **r.data} for r in results]
    return pd.DataFrame(rows)
