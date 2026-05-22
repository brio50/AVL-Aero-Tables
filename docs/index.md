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

**The key idea:** AVL is normally operated interactively — you type commands into its terminal menu, load a hand-written `.run` file, and step through each flight condition manually. `avl-aero-tables` bypasses this entirely. It invokes the AVL binary with no arguments and pipes a complete stdin script — loading geometry (`LOAD`), run-case (`CASE`), and all sweep commands (OPER, alpha/beta/deflection settings, `st` saves) — running hundreds of flight conditions in a single Python call.

Each sweep creates a timestamped subdirectory containing `results.csv`, a `provenance.json` record (git commit, dirty flag, source directory, snapshot path), AVL input snapshots in `.in/`, and raw `.st` output files in `.raw/` — so previous runs are never overwritten and every result is fully traceable. See {ref}`output-layout` for the full directory structure.

Five functions cover the full workflow — from reading a geometry file through plotting a finished aero database. Use the CLI for one-command runs, or call the Python API directly:

### CLI

Define a sweep in a YAML project file and run it in one command:

```bash
avl-aero-tables sweep examples/bd/bd.yml        # run sweep → _runs/bd/<timestamp>/
avl-aero-tables plot geometry examples/bd/bd.yml # four-view geometry plot
avl-aero-tables plot aero _runs/bd/              # plot latest sweep results
```

### Python API

Call the same steps programmatically:

```python
from avl_aero_tables import avl_fileread, avl_fileplot, avl_sweep, aero_filewrite, aero_fileplot

geom    = avl_fileread("examples/bd/bd.avl")           # parse geometry
fig     = avl_fileplot(geom)                        # four view of geometry
results = avl_sweep("examples/bd/bd.avl", alpha, beta, out_dir="_runs") # run AVL sweep
aero    = aero_filewrite(results)                   # build aero lookup tables
figs    = aero_fileplot(aero)                       # plot aero tables
```

```{seealso}
See {doc}`user/install` to get up and running, then {doc}`user/quickstart` for the full walkthrough.
```

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
dev/license
```
