# Usage

## Walkthrough: Bubble Dancer

[`bd.avl`](https://github.com/brio50/avl-aero-tables/blob/master/examples/bd.avl) is a sailplane with four control surfaces — flap, aileron, elevator, and rudder. This walkthrough follows the full pipeline from geometry to aero database.

### Read and plot the geometry

```python
from avl_aero_tables import avl_fileread, avl_fileplot

geom = avl_fileread("examples/bd.avl")

print(geom.header.name)          # Bubble Dancer RES
print(list(geom.surface.keys())) # ['Wing', 'Horizontal_tail', 'Vertical_tail']
print(geom.header.Sref)          # 1000.0  (reference area, sq-in)

fig = avl_fileplot(geom)
fig.savefig("bd_geometry.png", dpi=150)
```

![Bubble Dancer four-view geometry plot](../_static/img/bd_geometry.png)

### Run an alpha / beta sweep

```python
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=list(range(-6, 13, 2)),   # -6 to +12 deg, 2 deg steps
    beta=[0.0],
)

print(f"{len(results)} cases computed")
for r in results[:3]:
    print(f"  Alpha={r.data['Alpha']:5.1f}  CLtot={r.data['CLtot']:.4f}")
```

```
AVL sweep complete → /your/project/out/bd/2026-05-15-143022  (10 cases)
10 cases computed
  Alpha= -6.0  CLtot=-0.1669
  Alpha= -4.0  CLtot=0.0311
  Alpha= -2.0  CLtot=0.2299
```

### Sweep control surfaces

```python
results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, -5.0, 0.0, 5.0, 10.0]},
)
print(f"{len(results)} cases (4 alpha × 5 elevator deflections)")
```

```{note}
Surfaces in `ctrl_sweeps` are swept **independently**, not combinatorially. Two surfaces with five deflection points each produces 10 runs, not 25.
```

### Build an aero database

```python
from avl_aero_tables import aero_filewrite

results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=list(range(-6, 13, 2)),
    beta=[-6.0, -3.0, 0.0, 3.0, 6.0],
    ctrl_sweeps={"elevator": [-10.0, 0.0, 10.0]},
)

aero = aero_filewrite(results)

print(aero.stab["CLtot"].data.shape)               # (10, 5) — alpha × beta
print(aero.ctrl["CLtot_d03_elevator"].data.shape)  # (10, 5, 3) — alpha × beta × defl
```

```{important}
Stability tables (`aero.stab`) are populated **only for neutral-control runs** (all deflections = 0). Include `0.0` in every `ctrl_sweeps` deflection list or stability tables will be empty.
```

### Plot the aero database

```python
from avl_aero_tables import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
figs[0].savefig("bd_stab.png", dpi=150)        # stability coefficients
figs[1].savefig("bd_ctrl_CLtot.png", dpi=150)  # CLtot control derivatives
# figs[2..6] — CYtot, CDtot, Cltot, Cmtot, Cntot
```

![Bubble Dancer stability derivatives](../_static/img/bd_stab.png)

![Bubble Dancer CLtot control derivatives](../_static/img/bd_ctrl_fig1.png)

---

## Geometry

### Reading a geometry file

`avl_fileread()` parses an `.avl` file into an `AvlGeometry` dataclass containing a header, surfaces, and optional body definitions.

```python
from avl_aero_tables import avl_fileread

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
from avl_aero_tables import avl_fileplot

fig = avl_fileplot(geom)
fig.savefig("geometry.png", dpi=150)
```

### Custom geometry — recommended project layout

Keep your `.avl` file, `.mass` file, and any external airfoil coordinate files (`.dat`) together in one directory. `avl_sweep` sets AVL's working directory to the folder containing the `.avl` file, so all relative paths inside it resolve correctly regardless of where you run Python from.

```{code-block} text
:class: no-copybutton
📁 my_project/
├── 📁 geometry/
│   ├── 📄 my_aircraft.avl
│   ├── 📄 my_aircraft.mass   ← optional; mass & inertia breakdown
│   └── 📄 naca2412.dat       ← optional; external airfoil coordinates
├── 📁 out/                   ← generated at runtime
│   └── 📁 my_aircraft/
│       └── 📁 2026-05-15-143022/
└── 📄 analysis.py
```

```python
# analysis.py
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="geometry/my_aircraft.avl",
    alpha=list(range(-6, 13, 2)),
    beta=[-6.0, 0.0, 6.0],
    mass_file="my_aircraft.mass",   # bare filename → resolves relative to geometry/
)
```

## Running sweeps

### Alpha / beta sweep

The primary entry point is `avl_sweep()`. At minimum, supply an `.avl` file, `alpha`, and `beta` lists.

```python
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
)
```

### Control surface sweeps

`ctrl_sweeps` maps control surface names to deflection lists. Surfaces are swept **independently**, not combinatorially — matching the original MATLAB behaviour.

```python
results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={
        "elevator": [-10.0, -5.0, 0.0, 5.0, 10.0],
    },
)
```

````{warning}
Control surface names must match the `CONTROL` entries in the `.avl` file exactly. A `KeyError` is raised if a name is not found. Use `geom.ctrl_names` to list the available names:

```python
geom = avl_fileread("examples/bd.avl")
geom.ctrl_names  # ['flap', 'aileron', 'elevator', 'rudder']
```
````

### Mass and inertia

Pass a `.mass` file to load CG and inertia properties before the sweep. AVL receives it as a third CLI argument (`avl <avl_file> <reset.run> <mass_file>`).

```python
results = avl_sweep(
    avl_file="examples/bd.avl",
    alpha=list(range(-6, 13, 2)),
    beta=[0.0],
    mass_file="examples/bd.mass",   # bare filename resolves relative to the .avl directory
)
```

A bare filename resolves relative to the directory containing the `.avl` file. An absolute path also works — keep it short to stay within AVL's ~80-character Fortran string limit.

### Custom AVL binary

By default, `avl_sweep` auto-detects the AVL binary (`~/bin/avl`, then PATH). Override with `binary`:

```python
results = avl_sweep("examples/bd.avl", alpha=[-4, 0, 4], beta=[0], binary="/opt/avl/avl")
```

### Output format

The `out_format` parameter controls what file is written alongside the `.st` outputs:

| Value | Behaviour |
|---|---|
| `"csv"` (default) | Writes `out_dir/results.csv` |
| `"json"` | Writes `out_dir/results.json` |
| `"df"` | Returns a DataFrame; no file written |

```python
results = avl_sweep("examples/bd.avl", alpha=[-4, 0, 4], beta=[0], out_format="json")
```

### Output directory

By default, each call creates a timestamped subdirectory under 📁 `out/<geometry_name>/` so that previous results are never overwritten:

```{code-block} text
:class: no-copybutton
📁 out/
└── 📁 bd/
    └── 📁 2026-05-15-143022/
        ├── 📄 reset.run       ← AVL run-case file passed as CLI arg; all flight conditions zeroed
        ├── 📄 sweep.log       ← record of stdin commands fed to AVL; replay comment at top
        ├── 📄 case_0001.st
        ├── 📄 case_0002.st
        ├── 📄 ...
        └── 📄 results.csv
```

`reset.run` is in AVL's native `.run` format with all flight conditions zeroed — it is passed to the AVL binary as a CLI argument so that run-case state is initialized before the sweep begins. `sweep.log` records the stdin commands (OPER, alpha/beta/deflection settings, `st` saves) piped to AVL after the CLI args are loaded. Its first line is a comment showing the exact replay invocation:

```bash
# avl bd.avl /path/to/out/bd/2026-05-15-143022/reset.run < /path/to/out/bd/2026-05-15-143022/sweep.log
```

Copy that line, adjust paths as needed, and run it from the directory containing `bd.avl`.

To write to a fixed location instead — useful in scripts where you want to overwrite the previous result — pass `out_dir` explicitly. Stale `.st` files are removed before the new run:

```python
results = avl_sweep("examples/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="out/bd/latest")
```

## Aero database

### Building lookup tables

`aero_filewrite()` pivots a `list[StResult]` into an `AeroDatabase` with separate numpy arrays for stability and control derivatives.

```{important}
Stability tables are populated **only for neutral-control runs** (all deflections = 0). Include `0.0` in every `ctrl_sweeps` deflection list or stability tables will be empty.
```

```python
from avl_aero_tables import aero_filewrite

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
from avl_aero_tables import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
```

`beta_ref` selects the beta slice used for the control derivative plots.

## CLI

```bash
# Verify AVL binary is installed and reachable
avl-aero-tables verify

# Pipe a hand-written command file directly to AVL stdin
avl-aero-tables run my_commands.txt
```
