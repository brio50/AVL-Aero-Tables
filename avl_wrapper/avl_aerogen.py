"""Orchestrate AVL geometry reading, sweep execution, and .st output parsing."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from avl_wrapper import avl_bin as avl_runner
from avl_wrapper.avl_fileread import AvlGeometry, avl_fileread
from avl_wrapper.avl_rungen import make_command
from avl_wrapper.st_fileread import StResult, st_fileread


def _extract_ctrl_names(geometry: AvlGeometry) -> list[str]:
    """Return ordered unique control-surface names from the geometry."""
    seen: dict[str, None] = {}
    for surf in geometry.surface.values():
        for section_names in surf.CONTROL.Name:
            for name in section_names:
                if name:
                    seen[name] = None
    return list(seen)


def run(
    avl_file: str | Path,
    alpha: list[float],
    beta: list[float],
    ctrl_sweeps: dict[str, list[float]] | None = None,
    out_dir: Path | None = None,
    binary: Path | None = None,
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

    Returns
    -------
    list[StResult]
        One StResult per .st output file produced.
    """
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
    ctrl_names = _extract_ctrl_names(geometry)

    # AVL has an ~80-char Fortran string limit for filenames.  Stage .st files
    # in a short /tmp directory, then move them to the caller's out_dir.
    with tempfile.TemporaryDirectory(prefix="avl_") as staging_str:
        staging = Path(staging_str)
        cmd_text = make_command(
            avl_name,
            list(alpha),
            list(beta),
            ctrl_names,
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

    return st_fileread(out_dir)
