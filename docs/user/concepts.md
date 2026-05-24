# Concepts

These concepts span multiple functions in the pipeline. Understanding them helps you set up sweeps correctly and interpret results without surprises.

(concepts:aero-coefficients)=
## Aerodynamic Coefficients

AVL reports all forces and moments as **dimensionless coefficients** normalized by the dynamic pressure and the reference geometry declared in the `.avl` file header.

### Reference Frames

Three right-handed frames are used in aero analysis — body, stability, and wind — each a rotation of the previous.

**Body axes ($x_b$, $y_b$, $z_b$)** — fixed to the airframe, independent of the flow, with $x_b$ out the nose, $y_b$ out the right (starboard) wing, and $z_b$ down through the belly.

**Stability axes ($x_s$, $y_s$, $z_s$)** — body axes tilted up by $\alpha$ about the $y_b$ axis, so that $x_s$ points into the freestream when sideslip is zero. AVL reports all forces and moments in this frame:

$$\begin{pmatrix}x_s\\y_s\\z_s\end{pmatrix} = \begin{pmatrix}\cos\alpha & 0 & \sin\alpha\\0 & 1 & 0\\-\sin\alpha & 0 & \cos\alpha\end{pmatrix} \begin{pmatrix}x_b\\y_b\\z_b\end{pmatrix}$$

**Wind axes ($x_w$, $y_w$, $z_w$)** — stability axes rotated by sideslip $\beta$ about the $z_s$ axis, so that $x_w$ is fully aligned with the relative wind in both the pitch and yaw planes:

$$\begin{pmatrix}x_w\\y_w\\z_w\end{pmatrix} = \begin{pmatrix}\cos\beta & -\sin\beta & 0\\\sin\beta & \cos\beta & 0\\0 & 0 & 1\end{pmatrix} \begin{pmatrix}x_s\\y_s\\z_s\end{pmatrix}$$

| Frame | Aligned with | Used for |
|-------|-------------|----------|
| Body ($x_b$, $y_b$, $z_b$) | Airframe geometry | Equations of motion, inertia |
| **Stability ($x_s$, $y_s$, $z_s$)** | Freestream in pitch only ($\beta = 0$ assumed) | **AVL output — all coefficients here** |
| Wind ($x_w$, $y_w$, $z_w$) | Full relative wind (both $\alpha$ and $\beta$) | True drag / lift / sideforce |

```{figure} ../_static/img/fig2.1-air_vehicle_frame.png
:alt: Air Vehicle Reference Frames
:align: center
Figure 2.1 — Air Vehicle Reference Frames ([Borra, 2012](https://digitalcommons.calpoly.edu/theses/713/))
```

```{figure} ../_static/img/fig2.2-axes_relationships.png
:alt: Axis Relationships: Body, Stability, and Wind Axes
:align: center
:width: 80%
Figure 2.2 — Axis Relationships: Body, Stability, and Wind Axes ([Borra, 2012](https://digitalcommons.calpoly.edu/theses/713/))
```

### Definitions

Let $q = \tfrac{1}{2}\rho V^2$ be dynamic pressure, $S_\text{ref}$ the reference wing area, $b$ the reference span (Bref), and $\bar{c}$ the mean aerodynamic chord (Cref).

| Symbol | Definition | Physical meaning |
|--------|-----------|-----------------|
| `CL` | $F_z \;/\; (q \cdot S_\text{ref})$ | Lift — force opposing gravity |
| `CY` | $F_y \;/\; (q \cdot S_\text{ref})$ | Side force — positive toward starboard |
| `CD` | $F_x \;/\; (q \cdot S_\text{ref})$ | Drag — force opposing freestream |
| `Cl` | $M_x \;/\; (q \cdot S_\text{ref} \cdot b)$ | Roll moment — positive right-wing-down |
| `Cm` | $M_y \;/\; (q \cdot S_\text{ref} \cdot \bar{c})$ | Pitch moment — positive nose-up |
| `Cn` | $M_z \;/\; (q \cdot S_\text{ref} \cdot b)$ | Yaw moment — positive nose-right |

Upper-case (CL, CY, CD) denotes forces; lower-case (Cl, Cm, Cn) denotes moments. This casing convention is standard throughout AVL output.

```{seealso}
**AVL documentation** (*avl_doc.txt*, section "Body, Stability and Wind Axes") — authoritative source for AVL's stability-axis reporting and the exact normalizations CD = $F_x/(q S_\text{ref})$, CL = $F_z/(q S_\text{ref})$, etc.
```

### Normalizing Forces & Moments

AVL normalizes forces and moments by dynamic pressure $q$ and reference geometry. The dimensional equivalents are:

```{math}
:label: eq-recover
\begin{aligned}
L &= C_L \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \\
Y &= C_Y \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \\
D &= C_D \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \\
\bar{L} &= C_l \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot b \\
\bar{M} &= C_m \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot \bar{c} \\
\bar{N} &= C_n \cdot \tfrac{1}{2}\rho V^2 \cdot S_\text{ref} \cdot b
\end{aligned}
```

where $L$, $Y$, $D$ are lift, side force, and drag; $\bar{L}$, $\bar{M}$, $\bar{N}$ are roll, pitch, and yaw moments — all in units consistent with the input geometry. These are exact at $\beta = 0$. For nonzero sideslip, $C_D$ and $C_Y$ require correction before scaling — see {eq}`eq-wind-coeffs`.

### Sideslip Correction

When $\beta \neq 0$, stability-axis `CD` and `CY` are not the true wind-axis drag and side force. AVL's stability axes account for angle of attack ($\alpha$) but not sideslip ($\beta$) — when $\beta \neq 0$, $x_s$ does *not* fully point into the relative wind. As a result, what AVL labels `CD` is not purely the force opposing the velocity vector, and `CY` is not purely the perpendicular side force.

Since the stability→wind rotation is about $z_s$, the z-component is unchanged — $C_L$ and $C_n$ are unaffected. The AVL documentation notes that $C_D$, $C_Y$, $C_l$, and $C_m$ are all affected when $\beta \neq 0$. The force corrections are:

```{math}
:label: eq-wind-coeffs
\begin{aligned}
C_{L,\text{wind}} &= C_L \\
C_{D,\text{wind}} &= C_D \cos\beta - C_Y \sin\beta \\
C_{Y,\text{wind}} &= C_D \sin\beta + C_Y \cos\beta
\end{aligned}
```

Substitute $C_{D,\text{wind}}$ and $C_{Y,\text{wind}}$ into {eq}`eq-recover` in place of $C_D$ and $C_Y$ to obtain the correct dimensional $D$ and $Y$ for your wind-axis EOM.

````{admonition} Example — β correction at typical sideslip
Applying {eq}`eq-wind-coeffs` with $\beta = 10°$, $C_D = 0.025$, $C_Y = -0.05$ (negative side force is typical for positive sideslip):

```{math}
\begin{aligned}
C_{L,\text{wind}} &= C_L \quad \text{(unchanged)}\\
C_{D,\text{wind}} &= 0.025\cos(10°) - (-0.05)\sin(10°) &= 0.0246 + 0.0087 &= 0.0333\\
C_{Y,\text{wind}} &= 0.025\sin(10°) + (-0.05)\cos(10°) &= 0.0043 - 0.0492 &= -0.0449
\end{aligned}
```

The stability-axis $C_D = 0.025$ **underestimates** the true wind-axis drag ($0.033$) by 33% — the negative side force has a component that adds to drag when projected onto the velocity direction. At realistic sideslip angles the error is not negligible.
````

```{important}
The aero tables store stability-axis coefficients exactly as AVL computed them — **do not pre-apply the β correction when building the table**. Apply it at force-computation time in the simulation, where $\beta$ is known.
```

## Sweep Types

### Aero Sweep

An alpha/beta sweep with no `ctrl_sweeps` is the computational equivalent of a wind tunnel run — the aircraft is held at a fixed configuration and the flow angles are varied. Each `(alpha, beta)` point is one tunnel condition.

```python
results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-5, 16, 5)),
    beta=list(range(-5, 6, 5)),
)
```

The result is the baseline aerodynamic map — CL, CD, Cm, CY, Cl, Cn across the flight envelope — stored in `aero.total_stab` after passing through `aero_filewrite`. Every other sweep type is referenced against this baseline.

### Control Sweeps

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

### Neutral Runs

A **neutral-control run** is a case where every control surface deflection is zero — the aircraft in its clean, undeflected configuration. These runs define the baseline aerodynamic map.

`aero_filewrite` populates four separate table stores:

- **`aero.total_stab`** — total coefficients (CLtot, CDtot, Cmtot, …) vs. α and β; filled **only** from neutral-control runs
- **`aero.total_ctrl`** — total coefficients indexed by α, β, and deflection angle; filled from all control-surface runs
- **`aero.stab_deriv`** — stability derivatives (CLa, CLb, CLp, …, Cnr) vs. α and β; filled **only** from neutral-control runs
- **`aero.ctrl_deriv`** — control derivatives (∂CL/∂δ, ∂Cm/∂δ, …) vs. α and β; filled **only** from neutral-control runs

This ensures that off-neutral sweeps (e.g. elevator at ±20°) do not corrupt the baseline maps.

````{important}
Include `0.0` in every `ctrl_sweeps` deflection list, or `aero.total_stab` will be empty.

```python
ctrl_sweeps = {
    "elevator": [-20.0, 0.0, 20.0],  # ✓ 0.0 present → stab tables populated
}
```
````

(concepts:output)=
## Output

(concepts:output-types)=
### Data Categories

Each AVL `.st` file contains three categories of data for its flight condition. `aero_filewrite` preserves all three in the `AeroDatabase`:

| Category | Example keys | Physical meaning | Simulation use |
|---|---|---|---|
| **Total coefficients** | `CLtot`, `CYtot`, `CDtot`, `Cltot`, `Cmtot`, `Cntot` | Integrated force/moment at the flight condition | Nonlinear 6-DOF table-lookup simulation |
| **Stability derivatives** | `CLa`, `CLb`, `CLp`, …, `Cnr` | ∂coef/∂(α, β, p', q', r') — linearised sensitivity to perturbations | Eigenmode analysis, control law design, linear simulation |
| **Control derivatives** | `CLd01`, `CYd01`, …, `Cnd{n}` | ∂coef/∂δ_surface — control-surface effectiveness per unit deflection | Handling qualities, linear autopilot design, control allocation |

```{note}
**Total coefficients** (`CLtot`, `CDtot`, …) are the integrated values at a specific (α, β, δ) point — they capture all nonlinear effects and are appropriate for 6-DOF table-lookup simulation.
**Stability and control derivatives** (`CLa`, `CLd01`, …) are linearised — they represent the slope at the operating point, not the total. They are the right tool for linear analysis (eigenvalues, loop gain, etc.) but should not be used as look-up coefficients in a nonlinear sim.
```

The three categories map to the three output files and three `plot` subcommands:

```
results_total.csv          → total + stability + control data (all cases)
results_deriv_stab.csv     → stability derivatives (neutral-control cases only)
results_deriv_ctrl.csv     → control derivatives (neutral-control cases only)
```

```
avl-aero-tables plot totals     _runs/bd/   # total coefficients
avl-aero-tables plot stab-deriv _runs/bd/   # stability derivatives
avl-aero-tables plot ctrl-deriv _runs/bd/   # control derivatives
avl-aero-tables plot all        _runs/bd/   # all three in one shot
```

(output-layout)=
### Directory Layout

Every sweep creates a timestamped subdirectory inside the `out_dir` you pass:

```python
results = avl_sweep("examples/bd/bd.avl", alpha=[-4, 0, 4], beta=[0], out_dir="_runs")
```

```{code-block} text
:class: no-copybutton filetree
📁 _runs/
└── 📁 bd_2026-05-15-143022/
    ├── 📄 results_total.csv         ← all cases: Alpha, Beta, CLtot, derivatives …
    ├── 📄 results_deriv_stab.csv   ← neutral-control stability derivatives
    ├── 📄 results_deriv_ctrl.csv   ← neutral-control control derivatives
    ├── 📄 provenance.json          ← git commit, dirty flag, source dir, snapshot path
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

#### `results.*`

Every sweep writes three tabular output files (or JSON equivalents) controlled by the `out_format` parameter:

| File | Contents | Rows |
|---|---|---|
| `results_total.csv` | All keys from every `.st` case — Alpha, Beta, CLtot, deflections, stability derivatives, control derivatives | All cases |
| `results_deriv_stab.csv` | Stability derivatives (CLa, CLb, CLp, …, Cnr) | Neutral-control cases only |
| `results_deriv_ctrl.csv` | Control derivatives (CLd01, CYd01, …) | Neutral-control cases only |

`out_format = "df"` skips all file writes and returns results in memory only.

#### `provenance.json`

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

#### `.in/`

AVL inputs generated by the package. `reset.run` is the AVL run-case file that initialises all flight conditions to zero before the sweep begins. `sweep.inp` is the exact stdin script piped to the AVL subprocess to produce the `.st` files in `.raw/`.

The `<stem>/` subfolder is a snapshot of all user-provided input files copied at run time: the `.avl` geometry file, the `.yml` project file (CLI only), and any airfoil or body coordinate `.dat` files referenced by `AFIL`/`BFIL` entries in the geometry. Together with `provenance.json`, this makes every run directory self-contained and reproducible even if the source files are later modified.

#### `.raw/`

Raw AVL output files written per flight condition (`case_0001.st`, `case_0002.st`, …). Each file contains all three output categories: total aerodynamic coefficients (CLtot, CDtot, …), stability derivatives (CLa, Clb, …), and control derivatives (CLd01, …). `st_fileread` parses these into `list[StResult]`; `aero_filewrite` pivots all three categories into structured `AeroDatabase` tables.

### Filename Limit

AVL is written in Fortran and has an internal string limit of approximately 80 characters for filenames. Paths that exceed this limit are silently truncated, producing wrong or missing output files.

To stay under the limit, `avl_sweep` stages `.st` output files in a short `/tmp` directory during the run, then moves them to the timestamped run directory after AVL exits. The temp directory is cleaned up automatically even if AVL crashes.

This means:
- `out_dir` paths can be as long as you like — AVL never sees them directly
