"""Orchestrate AVL geometry reading, sweep execution, and .st output parsing."""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import tomllib
import warnings
from datetime import datetime
from pathlib import Path
from typing import Literal

from avl_aero_tables import avl_bin as avl_runner
from avl_aero_tables.aero_filewrite import results_to_dataframe
from avl_aero_tables.avl_fileread import (
    AvlGeometry,
    StResult,
    avl_fileread,
    st_fileread,
)
from avl_aero_tables.avl_rungen import make_run_command, make_run_reset

_FORMATS = frozenset(("csv", "json", "df"))


def _ensure_neutral_in_sweeps(
    ctrl_sweeps: dict[str, list[float]],
) -> dict[str, list[float]]:
    missing = [
        k for k, vals in ctrl_sweeps.items() if not any(abs(v) < 1e-9 for v in vals)
    ]
    if missing:
        warnings.warn(
            f"ctrl_sweeps surfaces {missing} have no 0.0 deflection — "
            "inserting 0.0 so stability tables are populated.",
            UserWarning,
            stacklevel=3,
        )
        ctrl_sweeps = {
            k: sorted(vals + [0.0]) if k in missing else vals
            for k, vals in ctrl_sweeps.items()
        }
    return ctrl_sweeps

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _package_version() -> str:
    """Read version from pyproject.toml (source of truth); fall back to importlib."""
    if _PYPROJECT.exists():
        with _PYPROJECT.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    from importlib.metadata import version

    return version("avl-aero-tables")


def _git_info(cwd: Path) -> dict[str, object]:
    """Return git provenance metadata; values are None if not in a git repo."""

    def _run(*args: str) -> str:
        try:
            r = subprocess.run(
                args, capture_output=True, text=True, cwd=cwd, timeout=5
            )
            return r.stdout.strip() if r.returncode == 0 else ""
        except Exception:
            return ""

    commit = _run("git", "rev-parse", "--short", "HEAD") or None
    if commit is None:
        return {"git_commit": None, "git_branch": None, "git_dirty": None}
    branch = _run("git", "rev-parse", "--abbrev-ref", "HEAD") or None
    dirty = bool(_run("git", "status", "--porcelain"))
    return {"git_commit": commit, "git_branch": branch, "git_dirty": dirty}


def _referenced_dat_files(avl_file: Path, geometry: AvlGeometry) -> list[Path]:
    """Return existing .dat files referenced by AFIL/BFIL entries in the geometry."""
    avl_dir = avl_file.parent
    paths: list[Path] = []
    if geometry.body and geometry.body.bfile:
        p = avl_dir / geometry.body.bfile
        if p.exists():
            paths.append(p)
    seen: set[str] = set()
    for surf in geometry.surface.values():
        for section in surf.sections:
            if section.afile and section.afile not in seen:
                seen.add(section.afile)
                p = avl_dir / section.afile
                if p.exists():
                    paths.append(p)
    return paths


def run(
    avl_file: str | Path,
    alpha: list[float],
    beta: list[float],
    ctrl_sweeps: dict[str, list[float]] | None = None,
    out_dir: Path | str | None = None,
    binary: Path | None = None,
    out_format: Literal["csv", "json", "df"] = "csv",
    yml_file: Path | str | None = None,
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
    yml_file:
        Path to the .yml project file (CLI use only).  When provided,
        ``provenance.json`` records ``entry: "cli"`` and copies the .yml
        into ``.in/<avl_stem>/``.

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

    if yml_file is not None:
        yml_file = Path(yml_file).resolve()

    if ctrl_sweeps is None:
        ctrl_sweeps = {}

    ctrl_sweeps = _ensure_neutral_in_sweeps(ctrl_sweeps)

    if out_dir is None:
        raise TypeError(
            "out_dir is required — pass a base directory (e.g. Path('runs'))"
        )
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    run_dir = Path(out_dir).resolve() / f"{avl_file.stem}_{timestamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    in_dir = run_dir / ".in"
    raw_dir = run_dir / ".raw"
    in_src_dir = in_dir / avl_name
    in_dir.mkdir()
    raw_dir.mkdir()
    in_src_dir.mkdir()

    geometry = avl_fileread(avl_file)

    # AVL has an ~80-char Fortran string limit for filenames.  Stage .st files
    # and reset.run in a short /tmp directory so their paths stay within the
    # limit when written into the LOAD/CASE/st commands inside the stdin script.
    reset_run_content = make_run_reset(avl_name, geometry.ctrl_names)

    with tempfile.TemporaryDirectory(prefix="avl_") as staging_str:
        staging = Path(staging_str)

        (staging / "reset.run").write_text(reset_run_content)
        (in_dir / "reset.run").write_text(reset_run_content)

        cmd_text = make_run_command(
            list(alpha),
            list(beta),
            geometry.ctrl_names,
            ctrl_sweeps,
            staging,
            avl_file=avl_file.name,
            run_file=str(staging / "reset.run"),
        )

        # sweep.inp: human-readable record of the stdin script fed to AVL;
        # paths reference .raw/ (where .st files land) and .in/reset.run
        (in_dir / "sweep.inp").write_text(
            "# avl  [stdin]\n"
            + make_run_command(
                list(alpha),
                list(beta),
                geometry.ctrl_names,
                ctrl_sweeps,
                raw_dir,
                avl_file=str(avl_file),
                run_file=str(in_dir / "reset.run"),
            )
        )

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
            shutil.move(str(st_file), raw_dir / st_file.name)

    # Copy input files into .in/<avl_name>/ as a run snapshot
    shutil.copy2(avl_file, in_src_dir / avl_file.name)
    if yml_file is not None:
        shutil.copy2(yml_file, in_src_dir / yml_file.name)
    for dat_file in _referenced_dat_files(avl_file, geometry):
        shutil.copy2(dat_file, in_src_dir / dat_file.name)

    # provenance.json at run root
    entry = "cli" if yml_file is not None else "api"
    source_dir = yml_file.parent if yml_file is not None else avl_dir
    provenance: dict[str, object] = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "package_version": _package_version(),
        **_git_info(avl_dir),
        "entry": entry,
        "source": str(source_dir),
        "snapshot": f".in/{avl_name}/",
    }
    (run_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    results = st_fileread(raw_dir)

    if out_format != "df":
        df = results_to_dataframe(results)
        if out_format == "csv":
            df.to_csv(run_dir / "results.csv", index=False)
        elif out_format == "json":
            df.to_json(run_dir / "results.json", orient="records", indent=2)

    import avl_aero_tables as _pkg

    if _pkg.verbose:
        print(f"AVL sweep complete → {run_dir}  ({len(results)} cases)")
    return results
