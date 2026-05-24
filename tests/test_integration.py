"""End-to-end integration tests: CLI commands and Python API chain.

All tests that invoke the AVL binary are skipped when it is not installed.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest

from avl_aero_tables import (
    aero_fileplot,
    aero_filewrite,
    avl_fileplot,
    avl_fileread,
    avl_sweep,
)
from avl_aero_tables.avl_bin import find_avl
from avl_aero_tables.avl_cli import main

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_DIR = EXAMPLES / "bd"
BD_AVL = BD_DIR / "bd.avl"

# 3 alpha × 1 beta × 3 elevator deflections = 9 cases
_MINIMAL_YML = """\
input:
  geometry: bd.avl
sweep:
  alpha: [-5, 0, 5]
  beta: [0]
  ctrl_sweeps:
    elevator: [-5, 0, 5]
output:
  format: csv
"""


def _avl_installed() -> bool:
    try:
        find_avl()
        return True
    except FileNotFoundError:
        return False


avl_required = pytest.mark.skipif(
    not _avl_installed(), reason="AVL binary not installed"
)


@pytest.fixture(autouse=True)
def no_browser():
    with patch("webbrowser.open"):
        yield


@pytest.fixture()
def bd_tmp(tmp_path):
    """Copy the bd example geometry to tmp_path with a minimal fast yml."""
    shutil.copytree(BD_DIR, tmp_path / "bd")
    yml = tmp_path / "bd" / "bd.yml"
    yml.write_text(_MINIMAL_YML)
    return yml


# ---------------------------------------------------------------------------
# CLI — each command
# ---------------------------------------------------------------------------


@avl_required
def test_cli_verify():
    assert main(["verify"]) == 0


@avl_required
def test_cli_sweep(bd_tmp):
    assert main(["sweep", str(bd_tmp)]) == 0

    runs_dir = bd_tmp.parent.parent / "_runs" / bd_tmp.stem
    run_dirs = list(runs_dir.iterdir())
    assert len(run_dirs) == 1, "expected exactly one run directory"

    run_dir = run_dirs[0]
    assert (run_dir / "results.csv").exists()
    assert (run_dir / "provenance.json").exists()
    st_files = list((run_dir / ".raw").glob("*.st"))
    assert len(st_files) == 9, f"expected 9 cases, got {len(st_files)}"


def test_cli_plot_geometry(bd_tmp):
    assert main(["plot", "geometry", str(bd_tmp)]) == 0
    assert (bd_tmp.parent / "bd_geometry.html").exists()


@avl_required
def test_cli_plot_aero(bd_tmp):
    assert main(["sweep", str(bd_tmp)]) == 0

    runs_dir = bd_tmp.parent.parent / "_runs" / bd_tmp.stem
    assert main(["plot", "totals", str(runs_dir)]) == 0

    run_dir = next(runs_dir.iterdir())
    assert (run_dir / "total_stability.html").exists()
    assert (run_dir / "total_control_CL.html").exists()


# ---------------------------------------------------------------------------
# Python API chain
# ---------------------------------------------------------------------------


@avl_required
def test_python_api_chain(tmp_path):
    """avl_fileread → avl_fileplot → avl_sweep → aero_filewrite → aero_fileplot."""
    geom = avl_fileread(BD_AVL)
    assert geom.header.name
    assert geom.ctrl_names == ["flap", "aileron", "elevator", "rudder"]
    assert geom.header.Sref > 0

    fig = avl_fileplot(geom)
    assert fig is not None

    results = avl_sweep(
        avl_file=BD_AVL,
        alpha=[-5.0, 0.0, 5.0],
        beta=[0.0],
        ctrl_sweeps={"elevator": [-5.0, 0.0, 5.0]},
        out_dir=tmp_path,
    )
    assert len(results) == 9
    assert all("CLtot" in r.data for r in results)

    aero = aero_filewrite(results)
    assert aero is not None

    figs = aero_fileplot(aero)
    assert len(figs) > 0
