# Usage

## Geometry

### Reading a geometry file

`avl_fileread()` parses an `.avl` file into an `AvlGeometry` dataclass containing a header, surfaces, and optional body definitions.

```python
from avl_wrapper import avl_fileread

geom = avl_fileread("examples/bd.avl")

# Header fields
geom.header.name    # geometry name string
geom.header.Sref    # reference area
geom.header.Cref    # reference chord
geom.header.Bref    # reference span

# Surfaces — keyed by surface name
geom.surface.keys()  # dict_keys(['Wing', 'Horizontal_tail', 'Vertical_tail'])
```

### Plotting geometry

`avl_fileplot()` returns a matplotlib `Figure` with four orthographic views.

```python
from avl_wrapper import avl_fileplot

fig = avl_fileplot(geom)
fig.savefig("geometry.png", dpi=150)
```

## Running sweeps

### Alpha / beta sweep

The primary entry point is `avl()`. At minimum, supply an `.avl` file, `alpha`, and `beta` lists.

```python
from avl_wrapper import avl

results = avl(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
)
```

### Control surface sweeps

`ctrl_sweeps` maps control surface names to deflection lists. Surfaces are swept **independently**, not combinatorially — matching the original MATLAB behaviour.

```python
results = avl(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={
        "elevator": [-10.0, -5.0, 0.0, 5.0, 10.0],
    },
)
```

```{warning}
Control surface names must match the `CONTROL` entries in the `.avl` file exactly. A `KeyError` is raised if a name is not found. Call `avl_fileread()` first and inspect the geometry to confirm available names.
```

### Output format

The `out_format` parameter controls what file is written alongside the `.st` outputs:

| Value | Behaviour |
|---|---|
| `"csv"` (default) | Writes `out_dir/results.csv` |
| `"json"` | Writes `out_dir/results.json` |
| `"df"` | Returns a DataFrame; no file written |

```python
results = avl("examples/bd.avl", alpha=[-4, 0, 4], beta=[0], out_format="json")
```

### Output directory

By default, `.st` files go to `<avl_file_parent>/out/<geometry_name>/`. Override with `out_dir`:

```python
results = avl("examples/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="/tmp/my_run")
```

## Aero database

### Building lookup tables

`aero_filewrite()` pivots a `list[StResult]` into an `AeroDatabase` with separate numpy arrays for stability and control derivatives.

```{important}
Stability tables are populated **only for neutral-control runs** (all deflections = 0). Include `0.0` in every `ctrl_sweeps` deflection list or stability tables will be empty.
```

```python
from avl_wrapper import aero_filewrite

aero = aero_filewrite(results)

# Stability derivatives (alpha × beta grids, neutral controls only)
aero.stab["CLtot"].alpha       # breakpoint alpha array
aero.stab["CLtot"].beta        # breakpoint beta array
aero.stab["CLtot"].data        # shape (n_alpha, n_beta)

# Control derivatives (alpha × beta × deflection grids)
aero.ctrl["CLtot_d03_elevator"].data   # shape (n_alpha, n_beta, n_defl)
```

### Plotting

`aero_fileplot()` returns a list of matplotlib figures — surface plots of stability coefficients and control derivatives.

```python
from avl_wrapper import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
```

`beta_ref` selects the beta slice used for the control derivative plots.

## CLI

```bash
# Verify AVL binary is installed and reachable
avl-wrapper verify

# Pipe a hand-written command file directly to AVL stdin
avl-wrapper run my_commands.txt
```