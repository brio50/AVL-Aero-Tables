# avl_sweep

Top-level orchestrator. Calls `avl_fileread`, `avl_rungen`, `avl_bin`, and `st_fileread` in sequence. Exposed publicly as `avl_sweep()` via `avl_aero_tables.__init__`.

```{eval-rst}
.. automodule:: avl_aero_tables.avl_sweep
   :members:
   :undoc-members: False
   :show-inheritance:
```

## Parameter details

### ctrl_sweeps

Maps control surface names to deflection lists. Names must match the `CONTROL` entries in the `.avl` file exactly — use `avl_fileread(avl_file).ctrl_names` to list them.

```python
from avl_aero_tables import avl_fileread, avl_sweep

geom = avl_fileread("examples/bd/bd.avl")
print(geom.ctrl_names)  # ['flap', 'aileron', 'elevator', 'rudder']

results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, 0.0, 10.0]},
)
```

Surfaces are swept independently, not combinatorially. See {doc}`../../concepts` for case-count details and why `0.0` must be included for stability tables to populate.

### mass_file

Pass a `.mass` file to load CG and inertia properties. AVL receives it as a third CLI argument (`avl <avl_file> <reset.run> <mass_file>`).

A **bare filename** (no directory component) resolves relative to the directory containing the `.avl` file — the same working directory AVL uses. An absolute path also works.

```python
results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-5, 16, 5)),
    beta=list(range(-5, 6, 5)),
    mass_file="bd.mass",   # resolves to examples/bd/bd.mass
)
```

### out_format

Controls what summary file is written alongside the `.st` outputs:

| Value | Behaviour |
|---|---|
| `"csv"` (default) | Writes `out_dir/results.csv` |
| `"json"` | Writes `out_dir/results.json` |
| `"df"` | Returns a DataFrame; no file written |

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], out_format="json")
```

### out_dir

By default, each call creates a timestamped subdirectory under `out/<geometry_name>/` so previous results are never overwritten. Pass `out_dir` to write to a fixed location instead — stale `.st` files are removed before the new run:

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="out/bd/latest")
```

See {doc}`../../concepts` for the full output directory layout and how to replay a run from the terminal.

### binary

By default, `avl_sweep` auto-detects the AVL binary (`~/bin/avl`, then `PATH`). Override with `binary`:

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], binary="/opt/avl/avl")
```
