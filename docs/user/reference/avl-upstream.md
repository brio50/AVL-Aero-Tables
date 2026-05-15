# AVL Upstream Documentation

AVL (Athena Vortex Lattice) is developed by Mark Drela and Harold Youngren at MIT.

- **Homepage**: <https://web.mit.edu/drela/Public/web/avl/>

```{note}
**AVL file types**

- **`.avl`** — geometry definition: surfaces, sections, control surface hinges, and reference quantities. This is the primary input you author.
- **`.run`** — run-case definition: flight conditions (alpha, beta, control deflections). AVL's native format; `avl-aero-tables` generates equivalent command scripts programmatically via `avl_rungen`.
- **`.st`** — stability output written by AVL for each run case: force coefficients, stability derivatives, and control derivatives. One file per flight condition.
- **`.mass`** — mass and inertia definition: CG location, mass, and inertia tensor. Pass to `avl_sweep()` via `mass_file=` so AVL loads realistic inertia properties before running the sweep.
- **`.eig`** — eigenvalue output from AVL's dynamic stability analysis. Not used by `avl-aero-tables`.
```

The user guide below covers AVL's geometry format, run-case syntax, output quantities, and theoretical background for the vortex lattice method.

---

```{literalinclude} avl_doc.txt
```
