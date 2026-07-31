"""avl-aero-tables CLI entry point."""

from __future__ import annotations

import argparse
import logging
import re
import sys
import tomllib
from pathlib import Path

from avl_aero_tables._plot_config import MATHJAX_RETYPESET
from avl_aero_tables.avl_bin import verify
from avl_aero_tables.avl_config import load_config

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _package_version() -> str:
    if _PYPROJECT.exists():
        with _PYPROJECT.open("rb") as f:
            return str(tomllib.load(f)["project"]["version"])
    from importlib.metadata import version

    return version("avl-aero-tables")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="avl-aero-tables",
        description="Python wrapper for AVL (Athena Vortex Lattice)",
        epilog=(
            "Use --help on any subcommand for details, e.g.:\n"
            "  avl-aero-tables sweep --help"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--version", action="version", version=f"avl-aero-tables {_package_version()}"
    )
    p.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress progress output"
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

    _runs_help = (
        "Path to a sweep results directory, or a parent directory (latest run is used)"
    )

    totals_p = plot_sub.add_parser(
        "totals",
        help="3-D total-coefficient surfaces (CLtot, CDtot, …) from sweep results",
    )
    totals_p.add_argument("runs_dir", type=Path, help=_runs_help)
    totals_p.add_argument(
        "--beta-ref",
        type=float,
        default=0.0,
        metavar="DEG",
        help="Sideslip angle (deg) for control-surface slices (default: 0.0)",
    )

    stabderiv_p = plot_sub.add_parser(
        "stab-deriv",
        help="3-D stability-derivative surfaces (CLa, CLb, CLp, …) from sweep results",
    )
    stabderiv_p.add_argument("runs_dir", type=Path, help=_runs_help)

    ctrlderiv_p = plot_sub.add_parser(
        "ctrl-deriv",
        help="3-D control-derivative surfaces (CLd01, CYd01, …) from sweep results",
    )
    ctrlderiv_p.add_argument("runs_dir", type=Path, help=_runs_help)

    all_p = plot_sub.add_parser(
        "all",
        help="Generate all plots: totals, stab-deriv, and ctrl-deriv",
    )
    all_p.add_argument("runs_dir", type=Path, help=_runs_help)
    all_p.add_argument(
        "--beta-ref",
        type=float,
        default=0.0,
        metavar="DEG",
        help="Sideslip angle (deg) for control-surface slices (default: 0.0)",
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

    out_dir = yml.parent.parent / "_runs" / yml.stem

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


def _write_index_html(directory: Path) -> Path:
    """Write index.html listing every *.html in directory (excluding itself)."""
    html_files = sorted(p for p in directory.glob("*.html") if p.name != "index.html")
    items = "\n".join(
        f'    <li><a href="{p.name}">{p.stem}</a></li>' for p in html_files
    )
    index = directory / "index.html"
    index.write_text(
        f"<!DOCTYPE html>\n"
        f"<html><head><meta charset='utf-8'>"
        f"<title>{directory.name}</title>"
        f"<style>body{{font-family:monospace;padding:2em}}"
        f"li{{margin:.4em 0}}a{{text-decoration:none}}"
        f"a:hover{{text-decoration:underline}}"
        f"</style></head>\n"
        f"<body><h2>{directory.name}</h2><ul>\n{items}\n</ul></body></html>\n"
    )
    return index


def _cmd_plot_geometry(args: argparse.Namespace) -> int:
    import webbrowser

    from avl_aero_tables.avl_fileplot import avl_fileplot
    from avl_aero_tables.avl_fileread import avl_fileread

    yml = args.yml.resolve()
    cfg = load_config(yml)
    avl_file = (yml.parent / cfg.input.geometry).resolve()

    geometry = avl_fileread(avl_file)
    fig = avl_fileplot(geometry)
    out = avl_file.parent / f"{avl_file.stem}_geometry.html"
    fig.write_html(
        str(out),
        include_plotlyjs="cdn",
        include_mathjax="cdn",
        post_script=MATHJAX_RETYPESET,
        config={"displayModeBar": True},
    )
    print(f"Geometry plot → {out}")
    index = _write_index_html(out.parent)
    webbrowser.open(index.as_uri())
    return 0


_TIMESTAMP_RE = re.compile(r".*\d{4}-\d{2}-\d{2}-\d{6}$")


def _resolve_result_dir(runs_dir: Path) -> Path | None:
    """Return the timestamped run directory, or None if not found."""
    is_run_dir = (
        re.search(r"\d{4}-\d{2}-\d{2}-\d{6}", runs_dir.name)
        or (runs_dir / ".raw").is_dir()
    )
    if is_run_dir:
        return runs_dir
    subdirs = (
        sorted(
            d for d in runs_dir.iterdir() if d.is_dir() and _TIMESTAMP_RE.match(d.name)
        )
        if runs_dir.exists()
        else []
    )
    return subdirs[-1] if subdirs else None


def _load_aero(runs_dir: Path):  # type: ignore[return]
    """Resolve runs_dir to a result directory; return (result_dir, AeroDatabase)."""
    from avl_aero_tables.aero_filewrite import aero_filewrite
    from avl_aero_tables.avl_fileread import st_fileread

    result_dir = _resolve_result_dir(runs_dir)
    if result_dir is None:
        print(f"ERROR: No sweep results found in {runs_dir}.", file=sys.stderr)
        return None, None
    results = st_fileread(result_dir / ".raw")
    return result_dir, aero_filewrite(results)


def _cmd_plot_totals(args: argparse.Namespace) -> int:
    import webbrowser

    from avl_aero_tables.aero_fileplot import plot_totals

    result_dir, aero = _load_aero(args.runs_dir.resolve())
    if aero is None:
        return 1

    figs = plot_totals(aero, beta_ref=args.beta_ref)
    for key, fig in figs.items():
        out = result_dir / f"total_{key}.html"
        fig.write_html(
            str(out),
            include_plotlyjs="cdn",
            include_mathjax="cdn",
            post_script=MATHJAX_RETYPESET,
            config={"displayModeBar": True},
        )
        print(f"  → {out.name}")
    index = _write_index_html(result_dir)
    webbrowser.open(index.as_uri())
    return 0


def _cmd_plot_stab_deriv(args: argparse.Namespace) -> int:
    import webbrowser

    from avl_aero_tables.aero_fileplot import plot_stab_derivs

    result_dir, aero = _load_aero(args.runs_dir.resolve())
    if aero is None:
        return 1

    figs = plot_stab_derivs(aero)
    for key, fig in figs.items():
        out = result_dir / f"deriv_stab_{key}.html"
        fig.write_html(
            str(out),
            include_plotlyjs="cdn",
            include_mathjax="cdn",
            post_script=MATHJAX_RETYPESET,
            config={"displayModeBar": True},
        )
        print(f"  → {out.name}")
    index = _write_index_html(result_dir)
    webbrowser.open(index.as_uri())
    return 0


def _cmd_plot_all(args: argparse.Namespace) -> int:
    import webbrowser

    from avl_aero_tables.aero_fileplot import (
        plot_ctrl_derivs,
        plot_stab_derivs,
        plot_totals,
    )

    result_dir, aero = _load_aero(args.runs_dir.resolve())
    if aero is None:
        return 1

    all_figs = {}
    for key, fig in plot_totals(aero, beta_ref=args.beta_ref).items():
        all_figs[f"total_{key}"] = fig
    for key, fig in plot_stab_derivs(aero).items():
        all_figs[f"deriv_stab_{key}"] = fig
    for key, fig in plot_ctrl_derivs(aero).items():
        all_figs[f"deriv_ctrl_{key}"] = fig

    for stem, fig in all_figs.items():
        out = result_dir / f"{stem}.html"
        fig.write_html(
            str(out),
            include_plotlyjs="cdn",
            include_mathjax="cdn",
            post_script=MATHJAX_RETYPESET,
            config={"displayModeBar": True},
        )
        print(f"  → {out.name}")
    index = _write_index_html(result_dir)
    webbrowser.open(index.as_uri())
    return 0


def _cmd_plot_ctrl_deriv(args: argparse.Namespace) -> int:
    import webbrowser

    from avl_aero_tables.aero_fileplot import plot_ctrl_derivs

    result_dir, aero = _load_aero(args.runs_dir.resolve())
    if aero is None:
        return 1

    figs = plot_ctrl_derivs(aero)
    for key, fig in figs.items():
        out = result_dir / f"deriv_ctrl_{key}.html"
        fig.write_html(
            str(out),
            include_plotlyjs="cdn",
            include_mathjax="cdn",
            post_script=MATHJAX_RETYPESET,
            config={"displayModeBar": True},
        )
        print(f"  → {out.name}")
    index = _write_index_html(result_dir)
    webbrowser.open(index.as_uri())
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``avl-aero-tables`` CLI.

    Global flags:

    ``--help``
        Show a help message and exit (also works on every subcommand).

    ``--version``
        Print the installed package version and exit.

    Subcommands:

    ``verify``
        Check that the AVL binary is installed and runnable.

    ``sweep <yml>``
        Load a YAML project file and run the AVL sweep.

    ``plot geometry <yml>``
        Four-view geometry plot from the .avl file.

    ``plot totals [--beta-ref DEG] <runs_dir>``
        3-D total-coefficient surfaces (CLtot, CDtot, …) from sweep results.
        Pass a specific timestamped run directory, or a parent directory to use
        the latest run.  ``--beta-ref`` slices control-surface plots at the
        nearest available sideslip angle (default 0°).

    ``plot stab-deriv <runs_dir>``
        3-D stability-derivative surfaces (CLa, CLb, CLp, …, Cnr) — one
        figure per perturbation variable (α, β, p', q', r').

    ``plot ctrl-deriv <runs_dir>``
        3-D control-derivative surfaces (CLd01, CYd01, …) — one figure per
        control surface.

    ``plot all [--beta-ref DEG] <runs_dir>``
        Generate all plots (totals, stab-deriv, ctrl-deriv) in one shot.

    Example
    -------
    .. code-block:: shell

        avl-aero-tables --help
        avl-aero-tables --version
        avl-aero-tables verify
        avl-aero-tables sweep examples/bd/bd.yml
        avl-aero-tables plot geometry examples/bd/bd.yml
        avl-aero-tables plot totals _runs/bd/
        avl-aero-tables plot totals --beta-ref 5 _runs/bd/
        avl-aero-tables plot stab-deriv _runs/bd/
        avl-aero-tables plot ctrl-deriv _runs/bd/
        avl-aero-tables plot all _runs/bd/
        avl-aero-tables plot all --beta-ref 5 _runs/bd/
    """
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.quiet:
        logging.basicConfig(format="%(message)s", level=logging.INFO)

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
        if args.plot_command == "totals":
            return _cmd_plot_totals(args)
        if args.plot_command == "stab-deriv":
            return _cmd_plot_stab_deriv(args)
        if args.plot_command == "ctrl-deriv":
            return _cmd_plot_ctrl_deriv(args)
        if args.plot_command == "all":
            return _cmd_plot_all(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
