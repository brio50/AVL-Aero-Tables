"""End-to-end walkthrough: geometry → sweep → aero database → plots.

Run from anywhere:
    python examples/quickstart.py           # outputs to examples/runs/bd_<timestamp>/
    python examples/quickstart.py --docs    # also copies PNGs to docs/_static/img/

Requires AVL binary installed at ~/bin/avl.
"""

import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent   # examples/
BD_AVL = HERE / "bd/bd.avl"
DOCS_IMG = HERE.parent / "docs/_static/img"


def main(write_docs: bool = False) -> None:
    runs_dir = HERE / "runs"

    # ── Geometry ──────────────────────────────────────────────────────────────
    from avl_aero_tables import avl_fileread, avl_fileplot

    geom = avl_fileread(BD_AVL)
    print(f"Geometry: {geom.header.name}")
    print(f"  surfaces : {list(geom.surface.keys())}")
    print(f"  controls : {geom.ctrl_names}")
    print(f"  Sref={geom.header.Sref}  Cref={geom.header.Cref}  Bref={geom.header.Bref}")

    fig_geom = avl_fileplot(geom)

    # ── Sweep: alpha × beta × all control surfaces ────────────────────────────
    from avl_aero_tables import avl_sweep

    results = avl_sweep(
        BD_AVL,
        alpha=list(range(-5, 16, 5)),
        beta=list(range(-5, 6, 5)),
        ctrl_sweeps={
            "flap":     [-10.0, 0.0, 10.0],
            "aileron":  [-15.0, 0.0, 15.0],
            "elevator": [-20.0, 0.0, 20.0],
            "rudder":   [-20.0, 0.0, 20.0],
        },
        out_dir=runs_dir,
    )

    # avl_sweep created runs/bd_<timestamp>/ — find it as the most recent subdir
    run_dir = max(runs_dir.glob("bd_*/"))
    print(f"Output → {run_dir}")

    _save(fig_geom, run_dir / "bd_geometry.png", DOCS_IMG / "bd_geometry.png", write_docs)

    # ── Aero database ─────────────────────────────────────────────────────────
    from avl_aero_tables import aero_filewrite

    aero = aero_filewrite(results)
    print(f"\nAero database:")
    print(f"  stab CLtot : {aero.stab['CLtot'].data.shape}  (alpha × beta)")
    print(f"  ctrl CLtot : {aero.ctrl['CLtot_d03_elevator'].data.shape}  (alpha × beta × defl)")

    # ── Plots ─────────────────────────────────────────────────────────────────
    from avl_aero_tables import aero_fileplot

    figs = aero_fileplot(aero, beta_ref=0.0)
    names = ["bd_stab", "bd_ctrl_CLtot", "bd_ctrl_CYtot", "bd_ctrl_CDtot",
             "bd_ctrl_Cltot", "bd_ctrl_Cmtot", "bd_ctrl_Cntot"]
    for fig, name in zip(figs, names):
        _save(fig, run_dir / f"{name}.png", DOCS_IMG / f"{name}.png", write_docs)

    print(f"\nDone. All outputs in {run_dir}")
    if write_docs:
        print(f"Doc images updated in {DOCS_IMG}")


def _save(fig, run_path: Path, docs_path: Path, write_docs: bool) -> None:
    fig.savefig(run_path, dpi=150, bbox_inches="tight")
    print(f"  → {run_path.name}")
    if write_docs:
        fig.savefig(docs_path, dpi=150, bbox_inches="tight")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--docs", action="store_true",
        help="also write PNGs to docs/_static/img/",
    )
    args = parser.parse_args()
    main(write_docs=args.docs)
