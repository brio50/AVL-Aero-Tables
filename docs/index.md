# avl-wrapper

![Tests](https://github.com/brio50/avl-wrapper/actions/workflows/test.yml/badge.svg)

A Python wrapper for [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT). Drives AVL via stdin command scripts, parses its `.st` output, and returns structured Python data — no manual file editing required.

## About AVL

AVL is a vortex lattice method (VLM) solver for aerodynamic and flight-dynamic analysis of fixed-wing aircraft. It is developed and maintained by Mark Drela and Harold Youngren at MIT and is widely used in preliminary design for its speed and accuracy at low computational cost.

:::{important}
Before using this wrapper, read the upstream AVL documentation. Understanding AVL's geometry format, reference quantities, and output conventions is essential for setting up runs correctly and interpreting results.
:::

- [AVL User Primer](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf) — start here; covers geometry input, run cases, and output quantities
- [AVL homepage](https://web.mit.edu/drela/Public/web/avl/) — source code, full user guide, and release notes

## What it does

Five functions cover the full workflow — from reading a geometry file through plotting a finished aero database:

```python
from avl_wrapper import avl_fileread, avl_fileplot, avl_sweep, aero_filewrite, aero_fileplot

geom    = avl_fileread("examples/bd.avl")           # parse geometry
fig     = avl_fileplot(geom)                        # four view plot
results = avl_sweep("examples/bd.avl", alpha, beta) # run AVL sweep
aero    = aero_filewrite(results)                   # build lookup tables
figs    = aero_fileplot(aero)                       # plot aero database
```

See {doc}`getting-started` to install and run the full walkthrough.

```{toctree}
:hidden:
:maxdepth: 2
:caption: Users

getting-started
usage
api/index
reference/avl-upstream
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Developers

roadmap
contributing
changelog
```
