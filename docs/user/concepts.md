# Concepts

These concepts span multiple functions in the pipeline. Understanding them helps you set up sweeps correctly and interpret results without surprises.

(concepts:aero-coefficients)=
## Aerodynamic Coefficients

AVL reports all forces and moments as **dimensionless coefficients** normalized by the dynamic pressure and the reference geometry declared in the `.avl` file header.

### Axes: body → stability → wind

Three right-handed frames are used in aero analysis. Each is a rotation of the previous.

**Body axes (X, Y, Z)** — fixed to the airframe, independent of the flow:
- X: out the nose
- Y: out the right (starboard) wing
- Z: down through the belly

**Stability axes (x, y, z)** — body axes rotated nose-down by $\alpha$ about the body Y axis, so that x points into the freestream when sideslip is zero. AVL reports all forces and moments in this frame:

$$\begin{pmatrix}x\\y\\z\end{pmatrix}_\text{stab} = \begin{pmatrix}\cos\alpha & 0 & \sin\alpha\\0 & 1 & 0\\-\sin\alpha & 0 & \cos\alpha\end{pmatrix} \begin{pmatrix}X\\Y\\Z\end{pmatrix}_\text{body}$$

**Wind axes** — stability axes rotated by sideslip $\beta$ about the stability z axis, so that x is fully aligned with the relative wind in both the pitch and yaw planes:

$$\begin{pmatrix}x\\y\\z\end{pmatrix}_\text{wind} = \begin{pmatrix}\cos\beta & -\sin\beta & 0\\\sin\beta & \cos\beta & 0\\0 & 0 & 1\end{pmatrix} \begin{pmatrix}x\\y\\z\end{pmatrix}_\text{stab}$$

| Frame | Aligned with | Used for |
|-------|-------------|----------|
| Body (X, Y, Z) | Airframe geometry | Equations of motion, inertia |
| **Stability (x, y, z)** | Freestream in pitch only ($\beta = 0$ assumed) | **AVL output — all coefficients here** |
| Wind | Full relative wind (both $\alpha$ and $\beta$) | True drag / lift / sideforce |

### When $\beta \neq 0$: stability-axis CD and CY are not true drag and side force

This is a subtle but important point for simulation use.

AVL's stability axes account for angle of attack ($\alpha$) but not sideslip ($\beta$). When $\beta \neq 0$, the stability-axis x does *not* fully point into the relative wind — it is still rotated by $\beta$ away from it. As a result, what AVL labels `CD` is not purely the force opposing the velocity vector, and `CY` is not purely the perpendicular side force.

To recover the **true wind-axis forces**, apply the $\beta$ rotation to the stability-axis coefficients:

$$C_{D,\text{wind}} = C_D \cos\beta + C_Y \sin\beta$$

$$C_{Y,\text{wind}} = -C_D \sin\beta + C_Y \cos\beta$$

$$C_{L,\text{wind}} = C_L \qquad \text{(z-axis rotation leaves z unchanged)}$$

**Worked example** — $\beta = 10°$, $C_D = 0.025$, $C_Y = -0.05$:

$$C_{D,\text{wind}} = 0.025\cos(10°) + (-0.05)\sin(10°) = 0.0246 - 0.0087 = 0.0159$$

The uncorrected stability-axis drag is $0.025$ — the true wind-axis drag is $0.016$, a 37% overestimate. At realistic sideslip angles the error is not negligible.

**For simulation use**, compute dimensional forces in wind axes first, then rotate to body axes for the equations of motion (see Stevens & Lewis, *Aircraft Simulation and Control*, §2.4 for the complete body-axis force transformation):

$$D = C_{D,\text{wind}} \cdot qS \qquad L = C_L \cdot qS \qquad Y = C_{Y,\text{wind}} \cdot qS$$

$$\begin{pmatrix}F_X\\F_Y\\F_Z\end{pmatrix}_\text{body} = R_y(\alpha)\,R_z(\beta) \begin{pmatrix}-D\\Y\\-L\end{pmatrix}$$

```{important}
The aero tables store stability-axis coefficients exactly as AVL computed them — **do not pre-apply the β correction when building the table**. Apply it at force-computation time in the simulation, where $\beta$ is known.
```

```{seealso}
**B. L. Stevens & F. L. Lewis** — *Aircraft Simulation and Control*, 2nd ed. (Wiley, 2003).
§2.3 covers body, stability, and wind axis definitions and rotation matrices.
§2.4 derives the full body-axis aerodynamic force equations from wind-axis lift, drag, and side force.
This is the standard reference for 6DOF flight simulation and the source for the body-axis force transformation above.
```

### Definitions

Let $Q = \tfrac{1}{2}\rho V^2$ be dynamic pressure, $S_\text{ref}$ the reference wing area, $b$ the reference span (Bref), and $\bar{c}$ the mean aerodynamic chord (Cref).

| Symbol | Definition | Physical meaning |
|--------|-----------|-----------------|
| `CL` | $F_z \;/\; (Q \cdot S_\text{ref})$ | Lift — force opposing gravity |
| `CY` | $F_y \;/\; (Q \cdot S_\text{ref})$ | Side force — positive toward starboard |
| `CD` | $F_x \;/\; (Q \cdot S_\text{ref})$ | Drag — force opposing freestream |
| `Cl` | $M_x \;/\; (Q \cdot S_\text{ref} \cdot b)$ | Roll moment — positive right-wing-down |
| `Cm` | $M_y \;/\; (Q \cdot S_\text{ref} \cdot \bar{c})$ | Pitch moment — positive nose-up |
| `Cn` | $M_z \;/\; (Q \cdot S_\text{ref} \cdot b)$ | Yaw moment — positive nose-right |

Upper-case (CL, CY, CD) denotes forces; lower-case (Cl, Cm, Cn) denotes moments. This casing convention is standard throughout AVL output and the **Stability** plot tab's derivative matrix (e.g. CLa = $\partial C_L / \partial \alpha$).

### Recovering actual forces and moments

Rearrange each definition to get dimensional quantities:

$$F_L = C_L \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref}$$

$$F_Y = C_Y \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref}$$

$$F_D = C_D \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref}$$

$$M_\text{roll} = C_l \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot b$$

$$M_\text{pitch} = C_m \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot \bar{c}$$

$$M_\text{yaw} = C_n \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot b$$

## Neutral Runs

A **neutral-control run** is a case where every control surface deflection is zero — the aircraft in its clean, undeflected configuration. These runs define the baseline aerodynamic map.

`aero_filewrite` populates two separate table stores:

- **`aero.stab`** — aerodynamic coefficients (CL, CD, Cm, …) as functions of alpha and beta; filled **only** from neutral-control runs
- **`aero.ctrl`** — control derivatives (ΔCL/Δδ, …) as functions of alpha, beta, and deflection; filled from all runs

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

When `ctrl_sweeps` is provided, each surface's deflection list is swept **independently** across every `(alpha, beta)` point — **not** as a full factorial combination of all surfaces simultaneously.

Each run deflects exactly one surface; all others remain at zero (neutral). This is equivalent to computing a finite-difference control derivative: $\Delta C_L / \Delta \delta_\text{elev}$ while holding rudder and aileron fixed.

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

```{note}
If you need a full combinatorial sweep (every elevator × every rudder deflection), run `avl_sweep` multiple times or build the `ctrl_sweeps` product yourself before calling it.
```

(output-layout)=
## Output Layout

Every sweep creates a timestamped subdirectory inside the `out_dir` you pass:

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="_runs")
```

```{code-block} text
:class: no-copybutton filetree
📁 _runs/
└── 📁 bd_2026-05-15-143022/
    ├── 📄 results.csv       ← aero table output (format: csv / json / df)
    ├── 📄 provenance.json   ← git commit, dirty flag, source dir, snapshot path
    ├── 📁 .in/              ← AVL inputs generated by the package
    │   ├── 📄 reset.run     ← AVL run-case (all conditions zeroed)
    │   ├── 📄 sweep.inp     ← complete AVL stdin script
    │   └── 📁 bd/           ← snapshot of user input files at run time
    │       ├── 📄 bd.avl
    │       ├── 📄 bd.yml        ← (CLI only)
    │       └── 📄 *.dat         ← airfoil / body coordinate files
    └── 📁 .raw/             ← raw AVL output files
        └── 📄 case_*.st     ← per-case stability & control derivatives
```

Previous runs are never overwritten — each call to `avl_sweep` creates a fresh `{avl_stem}_{timestamp}/` directory inside `out_dir`.

### `results.*`

All sweep cases pivoted into a single flat table. The format is controlled by the `out_format` parameter: `"csv"` (default), `"json"`, or `"df"` (in-memory `DataFrame` only — no file written). The filename reflects the chosen format: `results.csv` or `results.json`.

### `provenance.json`

Records the git state at run time so you can always trace which version of your geometry produced a given set of results. This is most valuable months after a run — when you need to know whether a coefficient change was due to a geometry edit or a code change, or when reproducing a result for a report after the source files have moved on:

```json
{
  "timestamp": "2026-05-16T14:30:22",
  "package_version": "1.8.0",
  "git_commit": "abc1234",
  "git_branch": "main",
  "git_dirty": false,
  "entry": "api",
  "source": "/path/to/examples/bd/",
  "snapshot": ".in/bd/"
}
```

`entry` is `"cli"` when invoked via `$ avl-aero-tables sweep` (see {ref}`quickstart:cli`), `"api"` when called from Python (see {ref}`quickstart:python-api`). `source` is the input directory — the folder containing the `.avl` file and all referenced airfoil and body coordinate files. For CLI runs this is also where the `.yml` lives.

`snapshot` is always a relative path from the run directory to the frozen copy of those input files. When `git_dirty: true`, `snapshot` is the authoritative record of exactly what was used — `source` may have changed since the run.

### `.in/`

AVL inputs generated by the package. `reset.run` is the AVL run-case file that initialises all flight conditions to zero before the sweep begins. `sweep.inp` is the exact stdin script piped to the AVL subprocess to produce the `.st` files in `.raw/`.

The `<stem>/` subfolder is a snapshot of all user-provided input files copied at run time: the `.avl` geometry file, the `.yml` project file (CLI only), and any airfoil or body coordinate `.dat` files referenced by `AFIL`/`BFIL` entries in the geometry. Together with `provenance.json`, this makes every run directory self-contained and reproducible even if the source files are later modified.

### `.raw/`

Raw per-case stability and control derivative output files written by AVL (`case_0001.st`, `case_0002.st`, …). One file per flight condition. These are the direct solver outputs that `st_fileread` parses to produce `list[StResult]`.

## Filename Limit

AVL is written in Fortran and has an internal string limit of approximately 80 characters for filenames. Paths that exceed this limit are silently truncated, producing wrong or missing output files.

To stay under the limit, `avl_sweep` stages `.st` output files in a short `/tmp` directory during the run, then moves them to the timestamped run directory after AVL exits. The temp directory is cleaned up automatically even if AVL crashes.

This means:
- `out_dir` paths can be as long as you like — AVL never sees them directly
