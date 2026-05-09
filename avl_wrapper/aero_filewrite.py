"""Convert list[StResult] into structured aero lookup tables."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date as _date

import numpy as np

from avl_wrapper.st_fileread import StResult

COEF_NAMES = ("CLtot", "CYtot", "CDtot", "Cltot", "Cmtot", "Cntot")
REF_FIELDS = ("Sref", "Cref", "Bref", "Xref", "Yref", "Zref")


@dataclass
class StabTable:
    """2-D coefficient lookup table indexed by (alpha, beta).

    Populated only for runs where all control surfaces are at neutral (0 deg).
    """

    coef: str
    alpha: np.ndarray  # shape (n_alpha,), sorted unique
    beta: np.ndarray   # shape (n_beta,),  sorted unique
    data: np.ndarray   # shape (n_alpha, n_beta), NaN where unfilled


@dataclass
class CtrlTable:
    """3-D coefficient lookup table indexed by (alpha, beta, deflection)."""

    coef: str
    surface: str      # e.g. "d01_flap"
    ctrl_name: str    # e.g. "flap"
    alpha: np.ndarray
    beta: np.ndarray
    defl: np.ndarray  # shape (n_defl,), sorted unique deflections
    data: np.ndarray  # shape (n_alpha, n_beta, n_defl), NaN where unfilled


@dataclass
class AeroDatabase:
    """Aero coefficient tables built from a sweep of AVL .st results.

    stab[coef]          → StabTable for neutral-control cases
    ctrl[coef_surface]  → CtrlTable for control-deflection cases
    """

    date: str
    Sref: float = 0.0
    Cref: float = 0.0
    Bref: float = 0.0
    Xref: float = 0.0
    Yref: float = 0.0
    Zref: float = 0.0
    stab: dict[str, StabTable] = field(default_factory=dict)
    ctrl: dict[str, CtrlTable] = field(default_factory=dict)


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
        Output from avl_aerogen.run() or st_fileread().

    Returns
    -------
    AeroDatabase
        Structured lookup tables keyed by coefficient name (and surface name
        for control tables).
    """
    if not results:
        raise ValueError("results is empty")

    r0 = results[0]
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
        db.stab[coef] = StabTable(
            coef=coef,
            alpha=alpha_arr,
            beta=beta_arr,
            data=np.full((len(alpha_arr), len(beta_arr)), np.nan),
        )

    for d_idx, ctrl_name in ctrl_map.items():
        surf_key = f"{d_idx}_{ctrl_name}"
        defl_arr = surface_defls[d_idx]
        for coef in COEF_NAMES:
            db.ctrl[f"{coef}_{surf_key}"] = CtrlTable(
                coef=coef,
                surface=surf_key,
                ctrl_name=ctrl_name,
                alpha=alpha_arr,
                beta=beta_arr,
                defl=defl_arr,
                data=np.full((len(alpha_arr), len(beta_arr), len(defl_arr)), np.nan),
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
                db.stab[coef].data[ai, bi] = val
            for d_idx, ctrl_name in ctrl_map.items():
                surf_key = f"{d_idx}_{ctrl_name}"
                defl_val = r.data.get(ctrl_name, 0.0)
                di = _find_idx(surface_defls[d_idx], defl_val)
                db.ctrl[f"{coef}_{surf_key}"].data[ai, bi, di] = val

    return db
