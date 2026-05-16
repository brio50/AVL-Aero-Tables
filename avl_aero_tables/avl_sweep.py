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
    out_dir: Path | str | None = None,
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
        Required. Base directory under which the timestamped run directory is
        created: ``out_dir / "{avl_stem}_{YYYY-MM-DD-HHMMSS}"``.
        Created automatically (including parents) if it does not exist.
        Raises ``TypeError`` if omitted.
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
    >>> import tempfile, pathlib
    >>> from avl_aero_tables import avl_sweep
    >>> with tempfile.TemporaryDirectory() as tmp:
    ...     results = avl_sweep(  # doctest: +ELLIPSIS
    ...         "examples/bd/bd.avl",
    ...         alpha=[-5, 0, 5, 10],
    ...         beta=[0],
    ...         ctrl_sweeps={"elevator": [-10, 0, 10]},
    ...         out_dir=tmp,
    ...     )
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
        raise TypeError(
            "out_dir is required — pass a base directory (e.g. Path('runs'))"
        )
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    run_dir = Path(out_dir).resolve() / f"{avl_file.stem}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    geometry = avl_fileread(avl_file)

    # AVL has an ~80-char Fortran string limit for filenames.  Stage .st files
    # and reset.run in a short /tmp directory so their paths stay within the
    # limit when written into the LOAD/CASE/st commands inside the stdin script.
    reset_run_content = make_run_reset(avl_name, geometry.ctrl_names)

    with tempfile.TemporaryDirectory(prefix="avl_") as staging_str:
        staging = Path(staging_str)

        (staging / "reset.run").write_text(reset_run_content)
        # reference copy in run_dir alongside results
        (run_dir / "reset.run").write_text(reset_run_content)

        cmd_text = make_run_command(
            list(alpha),
            list(beta),
            geometry.ctrl_names,
            ctrl_sweeps,
            staging,
            avl_file=avl_file.name,
            run_file=str(staging / "reset.run"),
        )

        # sweep.log: exact stdin script fed to AVL via subprocess; full paths
        # for human readability (AVL never sees this copy)
        (run_dir / "sweep.log").write_text(
            f"# avl  [stdin → {run_dir / 'sweep.log'}]\n"
            + make_run_command(
                list(alpha),
                list(beta),
                geometry.ctrl_names,
                ctrl_sweeps,
                run_dir,
                avl_file=str(avl_file),
                run_file=str(run_dir / "reset.run"),
            )
        )

        # .mass files are only needed for dynamic stability (.eig) output,
        # which is not part of this package's scope.
        result = avl_runner.run(
            cmd_text,
            binary=binary,
            cwd=avl_dir,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"AVL exited with code {result.returncode}.\n"
                f"stdout (last 2000 chars):\n{result.stdout[-2000:]}\n"
                f"stderr:\n{result.stderr[-2000:]}"
            )

        for st_file in sorted(staging.glob("*.st")):
            shutil.move(str(st_file), run_dir / st_file.name)

    results = st_fileread(run_dir)

    if out_format != "df":
        df = results_to_dataframe(results)
        if out_format == "csv":
            df.to_csv(run_dir / "results.csv", index=False)
        elif out_format == "json":
            df.to_json(run_dir / "results.json", orient="records", indent=2)

    print(f"AVL sweep complete → {run_dir}  ({len(results)} cases)")
    return results
