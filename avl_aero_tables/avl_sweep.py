"""Orchestrate AVL geometry reading, sweep execution, and .st output parsing."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from avl_aero_tables import avl_bin as avl_runner
from avl_aero_tables.aero_filewrite import results_to_dataframe
from avl_aero_tables.avl_fileread import avl_fileread
from avl_aero_tables.avl_rungen import make_run_command, make_run_reset
from avl_aero_tables.st_fileread import StResult, st_fileread

_FORMATS = frozenset(("csv", "json", "df"))


def run(
    avl_file: str | Path,
    alpha: list[float],
    beta: list[float],
    ctrl_sweeps: dict[str, list[float]] | None = None,
    out_dir: Path | None = None,
    binary: Path | None = None,
    out_format: Literal["csv", "json", "df"] = "csv",
    mass_file: str | Path | None = None,
) -> list[StResult]:
    """Run AVL stability analysis for a sweep of alpha, beta, and deflections.

    Parameters
    ----------
    avl_file:
        Path to the .avl geometry file.
    alpha:
        Angle-of-attack sweep values in degrees.
    beta:
        Sideslip angle sweep values in degrees.
    ctrl_sweeps:
        Mapping of control-surface name → deflection sweep values.
        An empty dict (default) produces one run per (alpha, beta) point.
    out_dir:
        Directory for .st output files.  Defaults to
        ``out/<geometry_name>/<timestamp>/`` relative to the current working
        directory, where timestamp is ``YYYY-MM-DD-HHMMSS``.  Each call
        creates a fresh subdirectory so previous results are never overwritten.
        Pass an explicit path to write to a fixed location instead.
    binary:
        Path to the AVL binary.  Auto-detected if not provided.
    out_format:
        Export format for results saved alongside the .st files.
        One of ``"csv"`` (default), ``"json"``,
        or ``"df"`` (DataFrame in memory only — no file written).
        The file is written to ``out_dir/results.<ext>``.
    mass_file:
        Optional path to a ``.mass`` file.  If provided, AVL loads the mass
        and inertia breakdown before running the sweep so that CG and inertia
        properties reflect the actual vehicle rather than the reset defaults.
        A bare filename (e.g. ``"bd.mass"``) resolves relative to the
        directory containing the ``.avl`` file.

    Returns
    -------
    list[StResult]
        One StResult per .st output file produced.

    Example
    -------
    >>> from avl_aero_tables import avl_sweep
    >>> results = avl_sweep(  # doctest: +ELLIPSIS
    ...     "examples/bd.avl",
    ...     alpha=[-5, 0, 5, 10],
    ...     beta=[0],
    ...     ctrl_sweeps={"elevator": [-10, 0, 10]},
    ... )
    AVL sweep complete → ...  (12 cases)
    >>> len(results)  # 4 alpha × 3 elevator deflections
    12
    >>> results[0].data["Alpha"]
    -5.0
    """
    if out_format not in _FORMATS:
        raise ValueError(
            f"out_format {out_format!r} not recognised; choose from {sorted(_FORMATS)}"
        )
    avl_file = Path(avl_file).resolve()
    avl_dir = avl_file.parent
    avl_name = avl_file.stem

    if ctrl_sweeps is None:
        ctrl_sweeps = {}

    if out_dir is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        out_dir = Path("out") / avl_name / timestamp
        out_dir = Path(out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = Path(out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        for stale in out_dir.glob("*.st"):
            stale.unlink()

    geometry = avl_fileread(avl_file)

    # Resolve mass_file to an absolute path (used as CLI arg; cwd=avl_dir so a
    # bare filename also works when the mass file lives alongside the .avl).
    mass_arg: str | None = None
    if mass_file is not None:
        mass_path = Path(mass_file)
        if not mass_path.is_absolute():
            mass_path = (avl_dir / mass_path).resolve()
        mass_arg = str(mass_path) if mass_path.parent != avl_dir else mass_path.name

    # AVL has an ~80-char Fortran string limit for filenames.  Stage .st files
    # and reset.run in a short /tmp directory so their paths stay within the
    # limit when passed as CLI args or written into the command script.
    reset_run_content = make_run_reset(avl_name, geometry.ctrl_names)

    with tempfile.TemporaryDirectory(prefix="avl_") as staging_str:
        staging = Path(staging_str)

        # reset.run in staging: short path for the CLI arg
        (staging / "reset.run").write_text(reset_run_content)
        # reference copy in out_dir alongside results
        (out_dir / "reset.run").write_text(reset_run_content)

        cmd_text = make_run_command(
            list(alpha),
            list(beta),
            geometry.ctrl_names,
            ctrl_sweeps,
            staging,
        )

        # sweep.log: human-readable record with a replay comment at the top
        mass_part = f" {mass_arg}" if mass_arg else ""
        replay = (
            f"# avl {avl_file.name} {out_dir / 'reset.run'}{mass_part}"
            f" < {out_dir / 'sweep.log'}"
        )
        (out_dir / "sweep.log").write_text(
            replay
            + "\n"
            + make_run_command(
                list(alpha),
                list(beta),
                geometry.ctrl_names,
                ctrl_sweeps,
                out_dir,
            )
        )

        result = avl_runner.run(
            cmd_text,
            binary=binary,
            cwd=avl_dir,
            avl_file=avl_file.name,
            run_file=str(staging / "reset.run"),
            mass_file=mass_arg,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"AVL exited with code {result.returncode}.\n"
                f"stdout (last 2000 chars):\n{result.stdout[-2000:]}\n"
                f"stderr:\n{result.stderr[-2000:]}"
            )

        for st_file in sorted(staging.glob("*.st")):
            shutil.move(str(st_file), out_dir / st_file.name)

    results = st_fileread(out_dir)

    if out_format != "df":
        df = results_to_dataframe(results)
        if out_format == "csv":
            df.to_csv(out_dir / "results.csv", index=False)
        elif out_format == "json":
            df.to_json(out_dir / "results.json", orient="records", indent=2)

    print(f"AVL sweep complete → {out_dir}  ({len(results)} cases)")
    return results
