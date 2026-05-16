"""Bubble Dancer walkthrough: geometry → sweep → aero database → plots.

Run from anywhere:
    python examples/bd.py           # outputs to examples/runs/bd_<timestamp>/
    python examples/bd.py --docs    # also copies HTML to docs/_static/html/

Requires AVL binary installed at ~/bin/avl.
"""

import argparse
from pathlib import Path

HERE = Path(__file__).resolve().parent   # examples/
BD_AVL = HERE / "bd/bd.avl"
DOCS_HTML = HERE.parent / "docs/_static/html"


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

    run_dir = max(runs_dir.glob("bd_*/"))
    print(f"Output → {run_dir}")

    _save_html(fig_geom, run_dir / "bd_geometry.html", DOCS_HTML / "bd_geometry.html", write_docs)

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
    parser.add_argument("--docs", action="store_true", help="also write HTML to docs/_static/html/")
    args = parser.parse_args()
    main(write_docs=args.docs)
