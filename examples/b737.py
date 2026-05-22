"""Boeing 737-800 walkthrough: geometry → sweep → aero database → plots.

Run from anywhere:
    python examples/b737.py           # outputs to examples/_runs/b737_<timestamp>/
    python examples/b737.py --docs    # also copies HTML to docs/_static/html/

Requires AVL binary installed at ~/bin/avl.
"""

import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent   # examples/
B737_AVL = HERE / "b737/b737.avl"
DOCS_HTML = HERE.parent / "docs/_static/html"


def main(write_docs: bool = False) -> None:
    runs_dir = HERE / "_runs"

    # ── Geometry ──────────────────────────────────────────────────────────────
    from avl_aero_tables import avl_fileread, avl_fileplot

    geom = avl_fileread(B737_AVL)
    print(f"Geometry: {geom.header.name}")
    print(f"  surfaces : {list(geom.surface.keys())}")
    print(f"  controls : {geom.ctrl_names}")
    print(f"  Sref={geom.header.Sref}  Cref={geom.header.Cref}  Bref={geom.header.Bref}")

    fig_geom = avl_fileplot(geom)

    # ── Sweep: alpha × beta × all control surfaces ────────────────────────────
    from avl_aero_tables import avl_sweep

    results = avl_sweep(
        B737_AVL,
        alpha=list(range(-5, 16, 5)),
        beta=list(range(-5, 6, 5)),
        ctrl_sweeps={
            "slat":     [0.0, 5.0, 10.0],
            "flap":     [0.0, 10.0, 20.0],
            "aileron":  [-10.0, 0.0, 10.0],
            "elevator": [-10.0, 0.0, 10.0],
            "rudder":   [-10.0, 0.0, 10.0],
        },
        out_dir=runs_dir,
    )

    # avl_sweep created _runs/b737_<timestamp>/ — find it as the most recent subdir
    run_dir = max(runs_dir.glob("b737_*/"))
    print(f"Output → {run_dir}")

    _save_html(fig_geom, run_dir / "b737_geometry.html", DOCS_HTML / "b737_geometry.html", write_docs)

    # ── Aero database ─────────────────────────────────────────────────────────
    from avl_aero_tables import aero_filewrite

    aero = aero_filewrite(results)
    print(f"\nAero database:")
    print(f"  stab CLtot : {aero.stab['CLtot'].data.shape}  (alpha × beta)")
    print(f"  ctrl CLtot : {aero.ctrl['CLtot_d04_elevator'].data.shape}  (alpha × beta × defl)")

    # ── Plots ─────────────────────────────────────────────────────────────────
    from avl_aero_tables import aero_fileplot

    figs = aero_fileplot(aero, beta_ref=0.0)
    names = ["b737_stab", "b737_ctrl_force_lift", "b737_ctrl_force_side", "b737_ctrl_force_drag",
             "b737_ctrl_moment_roll", "b737_ctrl_moment_pitch", "b737_ctrl_moment_yaw"]
    for fig, name in zip(figs, names):
        _save_html(fig, run_dir / f"{name}.html", DOCS_HTML / f"{name}.html", write_docs)

    print(f"\nDone. All outputs in {run_dir}")
    if write_docs:
        print(f"Doc HTML updated in {DOCS_HTML}")


def _save_html(fig: object, run_path: Path, docs_path: Path, write_docs: bool) -> None:
    html = fig.to_html(include_plotlyjs="cdn", full_html=False)  # type: ignore[attr-defined]
    run_path.write_text(html)
    print(f"  → {run_path.name}")
    if write_docs:
        docs_path.parent.mkdir(parents=True, exist_ok=True)
        docs_path.write_text(html)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs", action="store_true",
        help="also write HTML to docs/_static/html/",
    )
    args = parser.parse_args()
    main(write_docs=args.docs)
