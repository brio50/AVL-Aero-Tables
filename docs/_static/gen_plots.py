"""Regenerate committed doc images for usage.md.

Run from anywhere:
    python docs/_static/gen_plots.py
"""

from pathlib import Path

from avl_aero_tables import (
    aero_fileplot,
    aero_filewrite,
    avl_fileplot,
    avl_fileread,
    avl_sweep,
)

_HERE = Path(__file__).resolve().parent          # docs/_static/
BD_AVL = _HERE.parent.parent / "examples/bd/bd.avl"
IMG = _HERE / "img"


def main() -> None:
    # --- geometry ---
    geom = avl_fileread(BD_AVL)
    avl_fileplot(geom).savefig(IMG / "bd_geometry.png", dpi=150, bbox_inches="tight")
    print("wrote bd_geometry.png")

    # --- full aero sweep ---
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
        mass_file="bd.mass",
        out_format="df",
    )
    aero = aero_filewrite(results)

    figs = aero_fileplot(aero, beta_ref=0.0)
    names = ["bd_stab", "bd_ctrl_CLtot", "bd_ctrl_CYtot", "bd_ctrl_CDtot",
             "bd_ctrl_Cltot", "bd_ctrl_Cmtot", "bd_ctrl_Cntot"]
    for fig, name in zip(figs, names):
        fig.savefig(IMG / f"{name}.png", dpi=150, bbox_inches="tight")
        print(f"wrote {name}.png")


if __name__ == "__main__":
    main()
