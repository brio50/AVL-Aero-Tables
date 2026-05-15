# aero_filewrite

Pivots a `list[StResult]` into an `AeroDatabase` containing numpy arrays shaped for stability and control derivative lookup tables.

```{eval-rst}
.. automodule:: avl_aero_tables.aero_filewrite
   :members:
   :undoc-members: False
   :show-inheritance:
```

## AeroDatabase structure

`aero_filewrite` returns an `AeroDatabase` with two table stores:

**`aero.stab`** — stability derivatives as functions of alpha and beta, populated from neutral-control runs only:

```python
aero.stab["CLtot"].alpha   # 1-D alpha breakpoint array
aero.stab["CLtot"].beta    # 1-D beta breakpoint array
aero.stab["CLtot"].data    # shape (n_alpha, n_beta)
```

**`aero.ctrl`** — control derivatives as functions of alpha, beta, and surface deflection, keyed by `"<coeff>_d<idx>_<surface>"`:

```python
aero.ctrl["CLtot_d03_elevator"].data   # shape (n_alpha, n_beta, n_defl)
```

```{important}
`aero.stab` is populated **only from neutral-control runs** — cases where every surface deflection is zero. Include `0.0` in every `ctrl_sweeps` deflection list or stability tables will be empty. See {doc}`../../concepts`.
```
