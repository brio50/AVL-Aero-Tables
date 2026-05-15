# avl-aero-tables

![Tests](https://github.com/brio50/avl-aero-tables/actions/workflows/test.yml/badge.svg)

## What is AVL?

AVL (Athena Vortex Lattice) is a vortex lattice method (VLM) solver for aerodynamic and flight-dynamic analysis of fixed-wing aircraft. It is developed and maintained by Mark Drela and Harold Youngren at MIT and is widely used in preliminary design for its speed and accuracy at low computational cost.

```{important}
Before using this wrapper, read the upstream AVL documentation. Understanding AVL's geometry format, reference quantities, and output conventions is essential for setting up runs correctly and interpreting results.

- [AVL User Primer [.pdf]](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf) — start here; covers geometry input, run cases, and output quantities
- [MIT AVL Homepage](https://web.mit.edu/drela/Public/web/avl/) — source code, full user guide, and release notes
```

## What is AVL Aero Tables?

A Python package that drives AVL via stdin command scripts, parses its `.st` output, and returns structured aerodynamic lookup tables — no manual file editing required.

Five functions cover the full workflow — from reading a geometry file through plotting a finished aero database:

```python
from avl_aero_tables import avl_fileread, avl_fileplot, avl_sweep, aero_filewrite, aero_fileplot

geom    = avl_fileread("examples/bd.avl")           # parse geometry
fig     = avl_fileplot(geom)                        # four view of geometry
results = avl_sweep("examples/bd.avl", alpha, beta) # run AVL sweep
aero    = aero_filewrite(results)                   # build aero lookup tables
figs    = aero_fileplot(aero)                       # plot aero tables
```

See {doc}`user/install` to get up and running, then {doc}`user/usage` for the full walkthrough.

```{toctree}
:hidden:
:maxdepth: 2
:caption: Users

user/install
user/usage
user/reference/index
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Developers

dev/roadmap
dev/contributing
dev/changelog
dev/license
```
