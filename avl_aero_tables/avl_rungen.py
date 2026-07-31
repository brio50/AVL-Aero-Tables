"""Generate AVL run-case and command files for alpha/beta/deflection sweeps."""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Literal


def make_run_reset(
    avl_name: str,
    ctrl_names: list[str],
    *,
    Mach: float = 0.0,
    CDoref: float = 0.0,
    Xref: float = 0.0,
    Yref: float = 0.0,
    Zref: float = 0.0,
    Lunit: str = "Lunit",
    Munit: str = "Munit",
    Tunit: str = "Tunit",
) -> str:
    """Return the content of a reset run-case file (all states zeroed).

    The reset run case is loaded into AVL before each sweep point to ensure
    a clean starting state.  ctrl_names is the ordered list of control surface
    names (e.g. ["flap", "aileron", "elevator", "rudder"]).

    Example
    -------
    >>> from avl_aero_tables.avl_rungen import make_run_reset
    >>> text = make_run_reset(
    ...     "bd",
    ...     ["flap", "aileron", "elevator", "rudder"],
    ...     CDoref=0.017,
    ...     Xref=3.4,
    ...     Zref=0.5,
    ... )
    >>> "Run case  1:  Reset bd" in text
    True
    >>> " CDo       =   0.01700" in text
    True
    """
    lines: list[str] = [
        "",
        " ---------------------------------------------",
        f" Run case  1:  Reset {avl_name}",
        "",
    ]
    for name in ["alpha", "beta", "pb/2V", "qc/2V", "rb/2V"]:
        lines.append(f" {name:<12} ->  {name:<11} =  {0:.5f}")
    for ctrl in ctrl_names:
        lines.append(f" {ctrl:<12} ->  {ctrl:<11} =  {0:.5f}")
    lines.append(" ")

    scalar_rows: list[tuple[str, float, str]] = [
        ("alpha", 0.0, "deg"),
        ("beta", 0.0, "deg"),
        ("pb/2V", 0.0, ""),
        ("qc/2V", 0.0, ""),
        ("rb/2V", 0.0, ""),
        ("CL", 0.0, ""),
        ("CDo", CDoref, ""),
        ("bank", 0.0, "deg"),
        ("elevation", 0.0, "deg"),
        ("heading", 0.0, "deg"),
        ("Mach", Mach, ""),
        ("velocity", 0.0, f"{Lunit}/{Tunit}"),
        ("density", 1.0, f"{Munit}/{Tunit}^3"),
        ("grav.acc.", 1.0, f"{Lunit}/{Tunit}^2"),
        ("turn_rad.", 0.0, Lunit),
        ("load_fac.", 1.0, ""),
        ("X_cg", Xref, Lunit),
        ("Y_cg", Yref, Lunit),
        ("Z_cg", Zref, Lunit),
        ("mass", 1.0, Munit),
        ("Ixx", 1.0, f"{Munit}-{Lunit}^2"),
        ("Iyy", 1.0, f"{Munit}-{Lunit}^2"),
        ("Izz", 1.0, f"{Munit}-{Lunit}^2"),
        ("Ixy", 0.0, f"{Munit}-{Lunit}^2"),
        ("Iyz", 0.0, f"{Munit}-{Lunit}^2"),
        ("Izx", 0.0, f"{Munit}-{Lunit}^2"),
        ("visc CL_a", 0.0, ""),
        ("visc CL_u", 0.0, ""),
        ("visc CM_a", 0.0, ""),
        ("visc CM_u", 0.0, ""),
    ]
    for param, val, unit in scalar_rows:
        lines.append(f" {param:<10}=   {val:.5f}     {unit}")

    return "\n".join(lines) + "\n"


def make_run_command(
    alpha: list[float],
    beta: list[float],
    ctrl_names: list[str],
    ctrl_sweeps: dict[str, list[float]],
    out_dir: Path,
    avl_file: str | Path,
    run_file: str | Path,
    mode: Literal["independent", "combinatorial"] = "independent",
) -> str:
    """Return the AVL stdin command script for a sweep.

    AVL is driven entirely via stdin — geometry and run-case are loaded with
    LOAD and CASE commands at the top of the script, followed by OPER commands
    for each sweep point.

    Parameters
    ----------
    alpha:
        List of angle-of-attack values in degrees.
    beta:
        List of sideslip angle values in degrees.
    ctrl_names:
        Ordered list of control-surface names matching AVL's D1, D2, … indices.
    ctrl_sweeps:
        Mapping from control-surface name to its deflection sweep values.
        Only surfaces present in this dict are swept; others stay at zero.
        An empty dict produces one run per (alpha, beta) point.
    out_dir:
        Directory where .st output files will be written.  May be an absolute
        or relative path — keep it short; AVL has an ~80-char filename limit.
    avl_file:
        Path to the .avl geometry file passed to the LOAD command.
    run_file:
        Path to the reset .run file passed to the CASE command.
    mode:
        ``"independent"`` (default): surfaces in ``ctrl_sweeps`` are swept one
        at a time — each case deflects a single surface with all others held
        at 0°.  This matches the original MATLAB behavior and is unchanged
        from prior releases.
        ``"combinatorial"``: one case is emitted per element of the Cartesian
        product of every surface's deflection list, with *all* swept surfaces
        deflected simultaneously in each case (AVL's ``OPER`` menu natively
        supports setting multiple ``Di`` variables before running a case).
        Case count grows as the product of each surface's number of
        deflection values, so use judiciously for many surfaces.

    Example
    -------
    >>> from pathlib import Path
    >>> from avl_aero_tables.avl_rungen import make_run_command
    >>> cmd = make_run_command(
    ...     alpha=[0.0, 5.0],
    ...     beta=[0.0],
    ...     ctrl_names=["flap", "aileron", "elevator", "rudder"],
    ...     ctrl_sweeps={},
    ...     out_dir=Path("/tmp/avl_out"),
    ...     avl_file="bd.avl",
    ...     run_file="/tmp/avl_x/reset.run",
    ... )
    >>> cmd.splitlines()[0]
    'LOAD bd.avl'
    >>> cmd.count("A A")  # one alpha line per case
    2

    >>> cmd = make_run_command(
    ...     alpha=[0.0],
    ...     beta=[0.0],
    ...     ctrl_names=["flap", "aileron", "elevator", "rudder"],
    ...     ctrl_sweeps={"elevator": [-5.0, 0.0, 5.0], "rudder": [-10.0, 0.0, 10.0]},
    ...     out_dir=Path("/tmp/avl_out"),
    ...     avl_file="bd.avl",
    ...     run_file="/tmp/avl_x/reset.run",
    ...     mode="combinatorial",
    ... )
    >>> cmd.count("A A")  # 1 alpha × 1 beta × (3 elevator × 3 rudder) cases
    9
    """
    if mode not in ("independent", "combinatorial"):
        raise ValueError(
            f"mode {mode!r} not recognised; choose 'independent' or 'combinatorial'"
        )

    out_dir = Path(out_dir)
    lines: list[str] = [f"LOAD {avl_file}", f"CASE {run_file}", "PLOP", "G", "", "OPER"]

    case_num = 0

    if mode == "combinatorial" and ctrl_sweeps:
        combo_names = [name for name in ctrl_sweeps if name in ctrl_names]
        combo_indices = [ctrl_names.index(name) + 1 for name in combo_names]
        combo_values = [ctrl_sweeps[name] for name in combo_names]
        for a in alpha:
            for b in beta:
                for combo in itertools.product(*combo_values):
                    case_num += 1
                    st_path = out_dir / f"case_{case_num:04d}.st"
                    lines.append(f"A A {a:f}")
                    lines.append(f"B B {b:f}")
                    for surf_idx, defl in zip(combo_indices, combo):
                        lines.append(f"D{surf_idx} D{surf_idx} {defl:g}")
                    lines.extend(["i", "x", "st", str(st_path), "", "CINI", "OPER"])
        lines.extend(["", "Quit", ""])
        return "\n".join(lines)

    ctrl_points: list[tuple[int, float]] = [
        (ctrl_names.index(name) + 1, defl)
        for name, defl_vals in ctrl_sweeps.items()
        if name in ctrl_names
        for defl in defl_vals
    ]

    for a in alpha:
        for b in beta:
            if ctrl_points:
                for surf_idx, defl in ctrl_points:
                    case_num += 1
                    st_path = out_dir / f"case_{case_num:04d}.st"
                    lines.extend(
                        [
                            f"A A {a:f}",
                            f"B B {b:f}",
                            f"D{surf_idx} D{surf_idx} {defl:g}",
                            "i",
                            "x",
                            "st",
                            str(st_path),
                            "",
                            "CINI",
                            "OPER",
                        ]
                    )
            else:
                case_num += 1
                st_path = out_dir / f"case_{case_num:04d}.st"
                lines.extend(
                    [
                        f"A A {a:f}",
                        f"B B {b:f}",
                        "i",
                        "x",
                        "st",
                        str(st_path),
                        "",
                        "CINI",
                        "OPER",
                    ]
                )

    lines.extend(["", "Quit", ""])
    return "\n".join(lines)
