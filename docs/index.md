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

A Python package that drives AVL programmatically and returns structured aerodynamic lookup tables.

**The key idea:** AVL is normally operated interactively — you type commands into its terminal menu, load a hand-written `.run` file, and step through each flight condition manually. `avl-aero-tables` bypasses this entirely. It invokes the AVL binary using its documented CLI interface — passing the geometry and run-case files as positional arguments — then pipes the sweep commands (OPER, alpha/beta/deflection settings, `st` saves) to AVL's stdin, running hundreds of flight conditions in a single Python call.

For each sweep, two files are written to a timestamped subdirectory of 📁 `out/` alongside the results, so previous runs are never overwritten:

- **`reset.run`** — the AVL run-case file passed as a CLI argument; all flight conditions zeroed so every sweep point starts from a clean state
- **`sweep.log`** — the stdin commands piped to AVL; its first line is a comment with the exact shell command needed to replay the run

```{note}
Because `reset.run` and `sweep.log` live alongside the `.st` outputs in each timestamped directory, the full inputs to AVL are always on disk. Open `sweep.log` and copy its first line to replay any run manually from a terminal.
```

Five functions cover the full workflow — from reading a geometry file through plotting a finished aero database:

```python
from avl_aero_tables import avl_fileread, avl_fileplot, avl_sweep, aero_filewrite, aero_fileplot

geom    = avl_fileread("examples/bd/bd.avl")           # parse geometry
fig     = avl_fileplot(geom)                        # four view of geometry
results = avl_sweep("examples/bd/bd.avl", alpha, beta) # run AVL sweep
aero    = aero_filewrite(results)                   # build aero lookup tables
figs    = aero_fileplot(aero)                       # plot aero tables
```

See {doc}`user/install` to get up and running, then {doc}`user/quickstart` for the full walkthrough.

```{toctree}
:hidden:
:maxdepth: 2
:caption: Users

user/install
user/quickstart
user/concepts
user/reference/index
```

```{toctree}
:hidden:
:maxdepth: 1
:caption: Developers

dev/requirements
dev/roadmap
dev/contributing
dev/changelog
dev/license
```
