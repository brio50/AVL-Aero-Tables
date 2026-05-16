# Concepts

These concepts span multiple functions in the pipeline. Understanding them helps you set up sweeps correctly and interpret results without surprises.

## Neutral Runs

`aero_filewrite` populates two separate table stores:

- **`aero.stab`** — aerodynamic coefficients (CL, CD, Cm, …) as functions of alpha and beta
- **`aero.ctrl`** — control derivatives (ΔCL/Δδ, …) as functions of alpha, beta, and deflection

Stability tables are populated **only from neutral-control runs** — cases where every surface deflection is zero. This ensures that off-neutral sweeps (e.g. elevator at ±20°) do not corrupt the baseline aero map.

````{important}
Include `0.0` in every `ctrl_sweeps` deflection list, or `aero.stab` will be empty.

```python
ctrl_sweeps = {
    "elevator": [-20.0, 0.0, 20.0],  # ✓ 0.0 present → stab tables populated
}
```
````

## Aero Sweep

An alpha/beta sweep with no `ctrl_sweeps` is the computational equivalent of a wind tunnel run — the aircraft is held at a fixed configuration and the flow angles are varied. Each `(alpha, beta)` point is one tunnel condition.

```python
results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-5, 16, 5)),
    beta=list(range(-5, 6, 5)),
)
```

The result is the baseline aerodynamic map — CL, CD, Cm, CY, Cl, Cn across the flight envelope — stored in `aero.stab` after passing through `aero_filewrite`. Every other sweep type is referenced against this baseline.

## Control Sweeps

When `ctrl_sweeps` is provided, each surface's deflection list is swept **independently** across every `(alpha, beta)` point — not as a full combination of all surfaces.

The total case count is:

```
n_cases = n_alpha × n_beta × sum(len(deflections) for each surface)
```

Two surfaces with five deflection points each produces **10 runs per (alpha, beta) point**, not 25:

```python
ctrl_sweeps = {
    "elevator": [-10.0, -5.0, 0.0, 5.0, 10.0],   # 5 points
    "rudder":   [-10.0, -5.0, 0.0, 5.0, 10.0],   # 5 points
}
# → 10 ctrl points total, not 5×5=25
```

Each run deflects exactly one surface; all others stay at zero. This matches the original MATLAB implementation.

## Output Layout

Every sweep creates a timestamped subdirectory inside the `out_dir` you pass:

```{code-block} text
:class: no-copybutton filetree
📁 runs/
└── 📁 bd_2026-05-15-143022/
    ├── 📄 reset.run       ← AVL run-case file; all flight conditions zeroed
    ├── 📄 sweep.log       ← exact stdin commands fed to AVL via subprocess to produce these .st files
    ├── 📄 case_0001.st
    ├── 📄 case_0002.st
    ├── 📄 ...
    └── 📄 results.csv
```

Previous runs are never overwritten — each call to `avl_sweep` creates a fresh `{avl_stem}_{timestamp}/` directory inside `out_dir`:

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="runs")
```

`sweep.log` is the exact stdin command script that was fed to the AVL subprocess to produce the `.st` files in that directory. Its first line is a comment recording the AVL invocation:

```bash
# avl bd.avl /path/to/runs/bd_2026-05-15-143022/reset.run  [stdin → /path/to/runs/bd_2026-05-15-143022/sweep.log]
```

AVL is an interactive Fortran program — it has no CLI argument for a command script. `avl-aero-tables` drives it by piping this script to AVL's stdin via Python's `subprocess`. `sweep.log` is the on-disk record of exactly what was piped.

## Filename Limit

AVL is written in Fortran and has an internal string limit of approximately 80 characters for filenames. Paths that exceed this limit are silently truncated, producing wrong or missing output files.

To stay under the limit, `avl_sweep` stages `.st` output files in a short `/tmp` directory during the run, then moves them to the timestamped run directory after AVL exits. The temp directory is cleaned up automatically even if AVL crashes.

This means:
- `out_dir` paths can be as long as you like — AVL never sees them directly
