# AVL Upstream Documentation

AVL (Athena Vortex Lattice) is developed by Mark Drela and Harold Youngren at MIT.

- **Homepage**: <https://web.mit.edu/drela/Public/web/avl/>

```{note}
**AVL file types**

- **`.avl`** — geometry definition: surfaces, sections, control surface hinges, and reference quantities. This is the primary input you author.
- **`.run`** — run-case definition: flight conditions (alpha, beta, control deflections). AVL's native format; `avl-aero-tables` generates equivalent command scripts programmatically via `avl_rungen`.
- **`.st`** — stability output written by AVL for each run case: force coefficients, stability derivatives, and control derivatives. One file per flight condition.
- **`.mass`** — mass and inertia definition: CG location, mass, and inertia tensor. Only needed for dynamic stability eigenvalue analysis (`.eig`); `avl-aero-tables` does not use it.
- **`.eig`** — eigenvalue output from AVL's dynamic stability analysis. Not used by `avl-aero-tables`.
```

```{admonition} .mass files are not required
:class: tip

`avl-aero-tables` focuses on aerodynamic stability and control derivatives from `.st` outputs. These are computed by AVL's vortex lattice solver and **do not depend on mass or inertia properties** — the `.mass` file is only read by AVL when computing dynamic stability eigenvalues (phugoid, short-period, Dutch roll, etc.), which are written to `.eig` files. Since `avl-aero-tables` does not parse `.eig` output, no `.mass` file is needed.
```

The user guide below covers AVL's geometry format, run-case syntax, output quantities, and theoretical background for the vortex lattice method.

---

```{literalinclude} avl_doc.txt
```
