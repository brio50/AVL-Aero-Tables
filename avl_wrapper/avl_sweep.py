"""Orchestrate AVL geometry reading, sweep execution, and .st output parsing."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Literal

from avl_wrapper import avl_bin as avl_runner
from avl_wrapper.aero_filewrite import results_to_dataframe
from avl_wrapper.avl_fileread import avl_fileread
from avl_wrapper.avl_rungen import make_command
from avl_wrapper.st_fileread import StResult, st_fileread

_FORMATS = frozenset(("csv", "json", "df"))


def run(
    avl_file: str | Path,
    alpha: list[float],
    beta: list[float],
    ctrl_sweeps: dict[str, list[float]] | None = None,
    out_dir: Path | None = None,
    binary: Path | None = None,
    out_format: Literal["csv", "json", "df"] = "csv",
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
        <avl_file_parent>/out/<geometry_name>/.
    binary:
        Path to the AVL binary.  Auto-detected if not provided.
    out_format:
        Export format for results saved alongside the .st files.
        One of ``"csv"`` (default), ``"json"``,
        or ``"df"`` (DataFrame in memory only — no file written).
        The file is written to ``out_dir/results.<ext>``.

    Returns
    -------
    list[StResult]
        One StResult per .st output file produced.

    Example
    -------
    >>> from avl_wrapper import avl_sweep
    >>> results = avl_sweep.run(
    ...     "examples/bd.avl",
    ...     alpha=[-5, 0, 5, 10],
    ...     beta=[0],
    ...     ctrl_sweeps={"elevator": [-10, 0, 10]},
    ... )
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
        out_dir = avl_dir / "out" / avl_name
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    for stale in out_dir.glob("*.st"):
        stale.unlink()

    geometry = avl_fileread(avl_file)

    # AVL has an ~80-char Fortran string limit for filenames.  Stage .st files
    # in a short /tmp directory, then move them to the caller's out_dir.
    with tempfile.TemporaryDirectory(prefix="avl_") as staging_str:
        staging = Path(staging_str)
        cmd_text = make_command(
            avl_name,
            list(alpha),
            list(beta),
            geometry.ctrl_names,
            ctrl_sweeps,
            staging,
        )

        result = avl_runner.run(cmd_text, binary=binary, cwd=avl_dir)
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

    return results
