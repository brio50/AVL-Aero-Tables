# Python AVL Wrapper

![Tests](https://github.com/brio50/avl-aero-tables/actions/workflows/test.yml/badge.svg)

A Python wrapper for [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT). Drives AVL via stdin command scripts, parses its `.st` output, and returns structured Python data — no manual file editing required.

## Install

```bash
pip install avl-aero-tables
```

Requires Python 3.12+ and the AVL binary installed at `~/bin/avl`.

## Documentation

Full installation guide, walkthrough, API reference, and more at the [docs site](https://brio50.github.io/avl-aero-tables).

## Quick look

```python
from avl_aero_tables import avl_fileread, avl_fileplot, avl, aero_filewrite, aero_fileplot

geom    = avl_fileread("examples/bd.avl")          # parse geometry
fig     = avl_fileplot(geom)                        # four-view plot
results = avl("examples/bd.avl", alpha, beta)       # run AVL sweep
aero    = aero_filewrite(results)                   # build lookup tables
figs    = aero_fileplot(aero)                       # plot aero database
```

## References

- [AVL homepage](https://web.mit.edu/drela/Public/web/avl/)
- [AVL User Primer](https://web.mit.edu/drela/Public/web/avl/AVL_User_Primer.pdf)
