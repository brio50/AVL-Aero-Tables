# avl-aero-tables

![Tests](https://github.com/brio50/avl-aero-tables/actions/workflows/test.yml/badge.svg)

A Python package that drives [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT) programmatically — piping sweep commands to AVL's stdin, parsing its `.st` output, and returning structured aerodynamic lookup tables.

## Install

```bash
pip install avl-aero-tables
```

Requires Python 3.12+ and the AVL binary installed at `~/bin/avl`.

## Documentation

Full installation guide, walkthrough, API reference, and more at the [docs site](https://brio50.github.io/AVL-Aero-Tables/).

## Quick look

### CLI

Define a sweep in a YAML project file and run it in one command:

```console
$ avl-aero-tables sweep examples/bd/bd.yml         # run sweep → _runs/bd/<timestamp>/
$ avl-aero-tables plot geometry examples/bd/bd.yml  # interactive 3-D geometry plot
$ avl-aero-tables plot all _runs/bd/                # plot latest sweep results
```

### Python API

Call the same steps programmatically:

```python
from avl_aero_tables import avl_fileread, avl_fileplot, avl_sweep, aero_filewrite, plot_totals, plot_stab_derivs, plot_ctrl_derivs

geom    = avl_fileread("examples/bd/bd.avl")            # parse geometry
fig     = avl_fileplot(geom)                            # interactive 3-D plot
results = avl_sweep("examples/bd/bd.avl", alpha, beta, out_dir="_runs")  # run AVL sweep
aero    = aero_filewrite(results)                       # build lookup tables
figs_total = plot_totals(aero)                          # plot total aero tables
figs_stab  = plot_stab_derivs(aero)                    # plot stability derivatives
figs_ctrl  = plot_ctrl_derivs(aero)                    # plot control derivatives
```

## References

- [AVL homepage](https://web.mit.edu/drela/Public/web/avl/)
- [AVL User Primer](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf)
