"""Generate AVL run-case and command files for alpha/beta/deflection sweeps."""

from __future__ import annotations

from pathlib import Path


def make_reset_run(
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
    >>> from avl_wrapper.avl_rungen import make_reset_run
    >>> text = make_reset_run(
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


def make_command(
    avl_name: str,
    alpha: list[float],
    beta: list[float],
    ctrl_names: list[str],
    ctrl_sweeps: dict[str, list[float]],
    out_dir: Path,
) -> str:
    """Return the AVL interactive command script for a sweep.

    Parameters
    ----------
    avl_name:
        Geometry file stem without extension (e.g. "bd").
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

    Example
    -------
    >>> from pathlib import Path
    >>> from avl_wrapper.avl_rungen import make_command
    >>> cmd = make_command(
    ...     "bd",
    ...     alpha=[0.0, 5.0],
    ...     beta=[0.0],
    ...     ctrl_names=["flap", "aileron", "elevator", "rudder"],
    ...     ctrl_sweeps={},
    ...     out_dir=Path("/tmp/avl_out"),
    ... )
    >>> cmd.splitlines()[0]
    'LOAD bd'
    >>> cmd.count("A A")  # one alpha line per case
    2
    """
    out_dir = Path(out_dir)
    lines: list[str] = [f"LOAD {avl_name}", "PLOP", "G", "", "OPER"]

    ctrl_points: list[tuple[int, float]] = [
        (ctrl_names.index(name) + 1, defl)
        for name, defl_vals in ctrl_sweeps.items()
        if name in ctrl_names
        for defl in defl_vals
    ]

    case_num = 0
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
