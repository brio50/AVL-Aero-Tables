"""Convert list[StResult] into structured aero lookup tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

from avl_aero_tables.avl_fileread import StResult

if TYPE_CHECKING:
    import h5py
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


# ---------------------------------------------------------------------------
# External export (.mat / .h5) — optional dependencies, lazy-imported
# ---------------------------------------------------------------------------
#
# Shared hierarchy (identical field structure for both formats; "." separators
# below become "/" group paths in HDF5):
#
#   date, Sref, Cref, Bref, Xref, Yref, Zref     top-level scalars
#   breakpoints.alpha, breakpoints.beta          1-D arrays, shared by every
#                                                 total_stab/stab_deriv/ctrl_deriv
#                                                 table (identical by construction
#                                                 in aero_filewrite — stored once)
#   breakpoints.defl.<surface>                   1-D array, per control surface
#                                                 (e.g. "d01_flap") — varies by
#                                                 surface, so cannot live at the
#                                                 top level like alpha/beta
#   stab.<coef>                                  (n_alpha, n_beta), e.g. stab.CLtot
#   ctrl.<surface>.<coef>                        (n_alpha, n_beta, n_defl),
#                                                 e.g. ctrl.d01_flap.CLtot
#   stab_deriv.<key>                             (n_alpha, n_beta), e.g. stab_deriv.CLa
#   ctrl_deriv.<key>                             (n_alpha, n_beta),
#                                                 e.g. ctrl_deriv.CL_d01_flap
#
# stab_deriv/ctrl_deriv are included (not just total_stab/total_ctrl) so a
# MATLAB/Simulink consumer gets the full picture — derivatives are exactly as
# useful downstream as the totals and aero_filewrite already computes them.


def _breakpoints(db: AeroDatabase) -> tuple[np.ndarray, np.ndarray]:
    """Return the (alpha, beta) breakpoints shared by every table in db.

    total_stab/stab_deriv/ctrl_deriv/total_ctrl all share identical alpha/beta
    breakpoints by construction in aero_filewrite(), so the first non-empty
    table's axes are authoritative.
    """
    for tables in (db.total_stab, db.stab_deriv, db.ctrl_deriv):
        for table in tables.values():
            return table.alpha, table.beta
    for ctrl_table in db.total_ctrl.values():
        return ctrl_table.alpha, ctrl_table.beta
    raise ValueError(
        "AeroDatabase has no tables — cannot determine alpha/beta breakpoints"
    )


def _ctrl_by_surface(db: AeroDatabase) -> dict[str, dict[str, CtrlTable]]:
    """Group total_ctrl (keyed "<coef>_<surface>") into {surface: {coef: table}}."""
    out: dict[str, dict[str, CtrlTable]] = {}
    for table in db.total_ctrl.values():
        out.setdefault(table.surface, {})[table.coef] = table
    return out


def _db_to_nested_dict(db: AeroDatabase) -> dict[str, Any]:
    """Build the nested dict shared by aero_to_mat and aero_to_hdf5.

    scipy.io.savemat converts nested dicts into nested MATLAB structs directly;
    aero_to_hdf5 walks the same structure, turning nested dicts into HDF5
    groups and leaf arrays/scalars into datasets.
    """
    alpha, beta = _breakpoints(db)
    ctrl_by_surface = _ctrl_by_surface(db)

    out: dict[str, Any] = {"date": db.date}
    for fld in REF_FIELDS:
        out[fld] = float(getattr(db, fld))

    out["breakpoints"] = {
        "alpha": alpha,
        "beta": beta,
        "defl": {
            surface: next(iter(tables.values())).defl
            for surface, tables in ctrl_by_surface.items()
        },
    }
    out["stab"] = {coef: table.data for coef, table in db.total_stab.items()}
    out["ctrl"] = {
        surface: {coef: table.data for coef, table in tables.items()}
        for surface, tables in ctrl_by_surface.items()
    }
    out["stab_deriv"] = {key: table.data for key, table in db.stab_deriv.items()}
    out["ctrl_deriv"] = {key: table.data for key, table in db.ctrl_deriv.items()}
    return out


def aero_to_mat(db: AeroDatabase, path: str | Path) -> None:
    """Write an AeroDatabase to a MATLAB .mat file via scipy.io.savemat.

    Builds a nested dict — converted by savemat into nested MATLAB structs —
    mirroring the AeroDatabase hierarchy (see the module-level comment above
    _breakpoints for the exact field layout: date/Sref/.../breakpoints/stab/
    ctrl/stab_deriv/ctrl_deriv). Field/struct names are taken directly from
    AeroDatabase's own dict keys (coefficient names, "<d_idx>_<surface>" surface
    keys, derivative keys), all of which are already valid MATLAB identifiers.

    Requires the optional ``scipy`` dependency:
    ``pip install avl-aero-tables[export]``

    Parameters
    ----------
    db:
        AeroDatabase produced by aero_filewrite().
    path:
        Output .mat file path.

    Raises
    ------
    ImportError
        If scipy is not installed.
    ValueError
        If db has no tables to derive alpha/beta breakpoints from.
    """
    try:
        import scipy.io
    except ImportError as exc:
        raise ImportError(
            "aero_to_mat requires scipy — install with: "
            "pip install avl-aero-tables[export]"
        ) from exc

    scipy.io.savemat(str(path), _db_to_nested_dict(db))


def _write_h5_group(group: "h5py.Group", data: dict[str, Any]) -> None:
    for key, val in data.items():
        if isinstance(val, dict):
            _write_h5_group(group.create_group(key), val)
        else:
            group.create_dataset(key, data=val)


def aero_to_hdf5(db: AeroDatabase, path: str | Path) -> None:
    """Write an AeroDatabase to an HDF5 (.h5) file via h5py.

    Mirrors aero_to_mat's hierarchy with "/" group paths instead of MATLAB
    struct fields, e.g. /stab/CLtot, /ctrl/d01_flap/CLtot, /breakpoints/alpha,
    /breakpoints/defl/d01_flap, /stab_deriv/CLa, /ctrl_deriv/CL_d01_flap (see
    the module-level comment above _breakpoints for the exact field layout).
    Readable from MATLAB via ``h5read(path, "/stab/CLtot")``.

    Requires the optional ``h5py`` dependency:
    ``pip install avl-aero-tables[export]``

    Parameters
    ----------
    db:
        AeroDatabase produced by aero_filewrite().
    path:
        Output .h5 file path.

    Raises
    ------
    ImportError
        If h5py is not installed.
    ValueError
        If db has no tables to derive alpha/beta breakpoints from.
    """
    try:
        import h5py
    except ImportError as exc:
        raise ImportError(
            "aero_to_hdf5 requires h5py — install with: "
            "pip install avl-aero-tables[export]"
        ) from exc

    with h5py.File(str(path), "w") as f:
        _write_h5_group(f, _db_to_nested_dict(db))
