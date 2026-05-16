"""avl-aero-tables CLI entry point."""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path

from avl_aero_tables.avl_bin import verify
from avl_aero_tables.avl_config import load_config

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _package_version() -> str:
    if _PYPROJECT.exists():
        with _PYPROJECT.open("rb") as f:
            return tomllib.load(f)["project"]["version"]
    from importlib.metadata import version

    return version("avl-aero-tables")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="avl-aero-tables",
        description="Python wrapper for AVL (Athena Vortex Lattice)",
    )
    p.add_argument(
        "--version", action="version", version=f"avl-aero-tables {_package_version()}"
    )
    sub = p.add_subparsers(dest="command", required=True)

    sub.add_parser("verify", help="Check that the AVL binary is installed and works")

    sweep_p = sub.add_parser(
        "sweep", help="Run an AVL sweep defined by a YAML project file"
    )
    sweep_p.add_argument("yml", type=Path, help="Path to the .yml project file")

    plot_p = sub.add_parser("plot", help="Plot geometry or aero results")
    plot_sub = plot_p.add_subparsers(dest="plot_command", required=True)

    geom_p = plot_sub.add_parser(
        "geometry", help="Four-view geometry plot from the .avl file"
    )
    geom_p.add_argument("yml", type=Path, help="Path to the .yml project file")

    aero_p = plot_sub.add_parser(
        "aero", help="3-D aero coefficient surfaces from sweep results"
    )
    aero_p.add_argument(
        "runs_dir",
        type=Path,
        help="Path to a sweep results directory, or a parent directory (latest run is used)",
    )

    return p


def _cmd_sweep(args: argparse.Namespace) -> int:
    from avl_aero_tables.avl_sweep import run as _sweep_run

    yml = args.yml.resolve()
    cfg = load_config(yml)

    avl_file = (yml.parent / cfg.input.geometry).resolve()

    if cfg.sweep.ctrl_sweeps:
        from avl_aero_tables.avl_fileread import avl_fileread

        geom = avl_fileread(avl_file)
        valid = set(geom.ctrl_names)
        bad = [k for k in cfg.sweep.ctrl_sweeps if k not in valid]
        if bad:
            print(
                f"ERROR: ctrl_sweeps keys not found in {avl_file.name}: {bad}\n"
                f"  Valid control surfaces: {sorted(valid)}",
                file=sys.stderr,
            )
            sys.exit(1)

    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    out_dir = yml.parent.parent / "runs" / yml.stem / timestamp

    _sweep_run(
        avl_file=avl_file,
        alpha=cfg.sweep.alpha,
        beta=cfg.sweep.beta,
        ctrl_sweeps=cfg.sweep.ctrl_sweeps,
        out_dir=out_dir,
        out_format=cfg.output.format,
        yml_file=yml,
    )
    return 0


def _cmd_plot_geometry(args: argparse.Namespace) -> int:
    import matplotlib.pyplot as plt

    from avl_aero_tables.avl_fileplot import avl_fileplot
    from avl_aero_tables.avl_fileread import avl_fileread

    yml = args.yml.resolve()
    cfg = load_config(yml)
    avl_file = (yml.parent / cfg.input.geometry).resolve()

    geometry = avl_fileread(avl_file)
    avl_fileplot(geometry)
    plt.show()
    return 0


_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-\d{6}$")


def _cmd_plot_aero(args: argparse.Namespace) -> int:
    import matplotlib.pyplot as plt

    from avl_aero_tables.aero_fileplot import aero_fileplot
    from avl_aero_tables.aero_filewrite import aero_filewrite
    from avl_aero_tables.avl_fileread import st_fileread

    runs_dir = args.runs_dir.resolve()

    if _TIMESTAMP_RE.match(runs_dir.name):
        result_dir = runs_dir
    else:
        subdirs = (
            sorted(
                d
                for d in runs_dir.iterdir()
                if d.is_dir() and _TIMESTAMP_RE.match(d.name)
            )
            if runs_dir.exists()
            else []
        )
        if not subdirs:
            print(
                f"ERROR: No sweep results found in {runs_dir}.",
                file=sys.stderr,
            )
            return 1
        result_dir = subdirs[-1]

    results = st_fileread(result_dir / ".raw")
    aero = aero_filewrite(results)
    aero_fileplot(aero)
    plt.show()
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``avl-aero-tables`` CLI.

    Subcommands:

    ``verify``
        Check that the AVL binary is installed and runnable.

    ``sweep <yml>``
        Load a YAML project file and run the AVL sweep.

    ``plot geometry <yml>``
        Four-view geometry plot from the .avl file.

    ``plot aero <runs_dir>``
        3-D aero coefficient surfaces from sweep results. Pass a specific
        timestamped run directory, or a parent directory to use the latest run.

    Example
    -------
    .. code-block:: shell

        avl-aero-tables verify
        avl-aero-tables sweep examples/bd/bd.yml
        avl-aero-tables plot geometry examples/bd/bd.yml
        avl-aero-tables plot aero runs/bd/
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "verify":
        try:
            binary = verify()
            print(f"AVL binary OK: {binary}")
            return 0
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    if args.command == "sweep":
        return _cmd_sweep(args)

    if args.command == "plot":
        if args.plot_command == "geometry":
            return _cmd_plot_geometry(args)
        if args.plot_command == "aero":
            return _cmd_plot_aero(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
