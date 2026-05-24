# Quickstart

## Input Structure

An AVL geometry is a set of files that must travel together. The Bubble Dancer (`examples/bd/`) illustrates the typical structure — a sailplane with a fuselage body, four control surfaces (flap, aileron, elevator, rudder), and external airfoil coordinate files:

```{code-block} text
:class: no-copybutton filetree
📁 examples/bd/
├── 📄 bd.avl          ← geometry: surfaces, sections, control hinges, reference quantities
├── 📄 fuseBD.dat      ← fuselage body cross-section coordinates (referenced by bd.avl)
├── 📄 ag35.dat        ← airfoil coordinates (referenced by bd.avl AFIL entries)
├── 📄 ag36.dat
└── 📄 ag37.dat
```

## Project Layout

Keep all these files together. AVL's working directory is set to the folder containing the `.avl` file, so every relative path inside it (`fuseBD.dat`, `ag35.dat`, etc.) resolves automatically — relative to the `.avl` file, not your shell's current directory. Moving the `.avl` file without its companions will cause AVL to silently produce geometry with missing surfaces.

For your own project, keep geometry inputs versioned in git and runs outside of version control:

```{code-block} text
:class: no-copybutton filetree
📁 my_project/               ← git repo
├── 📁 _runs/                ← generated at runtime; add to .gitignore
│   └── 📁 design_2026-05-15-143022/
├── 📁 design/
│   ├── 📄 design.avl        ← geometry: surfaces, sections, control hinges
│   ├── 📄 wing_airfoil.dat  ← airfoil coordinates   (AFIL entry in .avl)
│   └── 📄 fuselage.dat      ← body cross-sections   (BFIL entry in .avl)
│   └── 📄 design.yml        ← CLI project file
├── 📄 analysis.py           ← Python API script
└── 📄 .gitignore            ← contains: _runs/
```

See {ref}`output-layout` for the full contents of each timestamped run directory.

(quickstart:cli)=
## CLI

% To update plots in this section: python examples/bd.py --docs

The fastest path from geometry to results — define your sweep in a YAML project file, then run three commands.

```{seealso}
- [examples/bd/bd.avl](https://github.com/brio50/avl-aero-tables/blob/master/examples/bd/bd.avl) — Bubble Dancer geometry with control surfaces and airfoil references
- [examples/bd/bd.yml](https://github.com/brio50/avl-aero-tables/blob/master/examples/bd/bd.yml) — project file driving the sweep below
- [examples/bd.py](https://github.com/brio50/avl-aero-tables/blob/master/examples/bd.py) — regenerates all plots in this section (`--docs` flag)
```

### Project File

Create a `bd.yml` alongside your `.avl` file:

```{code-block} yaml
:caption: examples/bd/bd.yml
input:
  geometry: bd.avl

sweep:
  alpha: [-5, 0, 5, 10, 15]
  beta: [0]
  ctrl_sweeps:
    elevator: [-10, -5, 0, 5, 10]
    rudder:   [-10, 0, 10]
    aileron:  [-10, 0, 10]

output:
  format: csv
```

`input.geometry` is a path relative to the `.yml` file, so they should live in the same directory.

### Plot Geometry

Check that AVL reads the geometry correctly before running a sweep:

`````{card}
:class-card: cli-card

```{code-block} console
:caption: Input
$ avl-aero-tables plot geometry examples/bd/bd.yml
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

```{plotly-figure} _static/html/bd_geometry.html
```
`````

```{tip}
The plots on this page are interactive thanks to [plot.ly](https://plotly.com/python/)! Play with the toolbar to the top right of the image, drag and rotate 3dScatter content.
```

### Run Sweep

`````{card}
:class-card: cli-card

```{code-block} console
:caption: Input
$ avl-aero-tables sweep examples/bd/bd.yml
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
AVL sweep complete → /your/project/examples/_runs/bd/bd_2026-05-20-191250  (55 cases)
```
`````

```{note}
While AVL runs, a Rich spinner (`⠹ Running AVL…`) animates in-place on the terminal — it disappears when the sweep finishes, leaving only the completion line.
Pass `--quiet` to suppress all console output.

Results land in `_runs/<yml-stem>/<avl-stem>_<timestamp>/` relative to the **project root** (one directory up from the `.yml` file). This differs from the Python API, where you control `out_dir` directly.
```

### Plot Results

AVL produces three categories of output per flight condition — each has its own `plot` subcommand. Pass a parent directory to use the latest sweep, or a specific timestamped directory to target a particular run.

See {ref}`concepts:output-types` for a full description of each category and its simulation use.

#### Total Coefficients

```{admonition} Nonlinear 6-DOF table-lookup
:class: note
Total force and moment coefficients ($C_{L_\mathrm{total}}$, $C_{D_\mathrm{total}}$, $C_{m_\mathrm{total}}$, …) integrated at each flight condition. These are the tables a nonlinear 6-DOF simulation queries at each timestep — the primary output for flight dynamics work.
```

```````{card}
:class-card: cli-card full-width

```{code-block} console
:caption: Input
$ avl-aero-tables plot totals _runs/bd/
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
  → total_stability.html
  → total_control_CL.html
  → total_control_CY.html
  → total_control_CD.html
  → total_control_Cl.html
  → total_control_Cm.html
  → total_control_Cn.html
```

`````{tab-set}
:class: aero-plots
````{tab-item} Stability
```{plotly-figure} _static/html/bd_total_stab.html
```
````
````{tab-item} CL
```{plotly-figure} _static/html/bd_total_ctrl_lift.html
```
````
````{tab-item} CY
```{plotly-figure} _static/html/bd_total_ctrl_side.html
```
````
````{tab-item} CD
```{plotly-figure} _static/html/bd_total_ctrl_drag.html
```
````
````{tab-item} Cl
```{plotly-figure} _static/html/bd_total_ctrl_roll.html
```
````
````{tab-item} Cm
```{plotly-figure} _static/html/bd_total_ctrl_pitch.html
```
````
````{tab-item} Cn
```{plotly-figure} _static/html/bd_total_ctrl_yaw.html
```
````
`````
```````

```{tip}
The "Stability" tab shows coefficients vs. $\alpha$ and $\beta$ at neutral controls. The $C_L$/$C_Y$/… tabs each show coefficient vs. $\alpha$ and $\delta$ for every control surface, sliced at **$\beta = 0°$** by default. To inspect a different sideslip, pass `--beta-ref <deg>` — e.g. `avl-aero-tables plot totals --beta-ref 5 _runs/bd/`.
```

#### Stability Derivatives

```{admonition} Linear analysis — stability derivatives, trim sensitivity, control law design
:class: note
Linearised $\partial C / \partial(\alpha, \beta, p', q', r')$ at neutral controls. One figure per perturbation variable, six subplots per figure ($C_L$, $C_Y$, $C_D$, $C_l$, $C_m$, $C_n$). Use these for stability analysis (phugoid, dutch roll), trim sensitivity, and linear control law derivation — not as table-lookup coefficients in a nonlinear sim.
```

```````{card}
:class-card: cli-card full-width

```{code-block} console
:caption: Input
$ avl-aero-tables plot stab-deriv _runs/bd/
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
  → deriv_stability_alpha.html
  → deriv_stability_beta.html
  → deriv_stability_p.html
  → deriv_stability_q.html
  → deriv_stability_r.html
```

`````{tab-set}
:class: aero-plots
````{tab-item} ∂/∂α
```{plotly-figure} _static/html/bd_deriv_stab_alpha.html
```
````
````{tab-item} ∂/∂β
```{plotly-figure} _static/html/bd_deriv_stab_beta.html
```
````
````{tab-item} ∂/∂p'
```{plotly-figure} _static/html/bd_deriv_stab_p.html
```
````
````{tab-item} ∂/∂q'
```{plotly-figure} _static/html/bd_deriv_stab_q.html
```
````
````{tab-item} ∂/∂r'
```{plotly-figure} _static/html/bd_deriv_stab_r.html
```
````
`````
```````

#### Control Derivatives

```{admonition} Control effectiveness — surface sizing, linear autopilot design
:class: note
Linearised $\partial C / \partial\delta_\text{surface}$ at neutral controls. One figure per control surface, six subplots per figure ($C_L$, $C_Y$, $C_D$, $C_l$, $C_m$, $C_n$ vs. $\alpha$ and $\beta$). Use these for control allocation, handling qualities assessment, and linear autopilot gain derivation.
```

```````{card}
:class-card: cli-card full-width

```{code-block} console
:caption: Input
$ avl-aero-tables plot ctrl-deriv _runs/bd/
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
  → deriv_control_flap.html
  → deriv_control_aileron.html
  → deriv_control_elevator.html
  → deriv_control_rudder.html
```

`````{tab-set}
:class: aero-plots
````{tab-item} flap
```{plotly-figure} _static/html/bd_deriv_ctrl_flap.html
```
````
````{tab-item} aileron
```{plotly-figure} _static/html/bd_deriv_ctrl_aileron.html
```
````
````{tab-item} elevator
```{plotly-figure} _static/html/bd_deriv_ctrl_elevator.html
```
````
````{tab-item} rudder
```{plotly-figure} _static/html/bd_deriv_ctrl_rudder.html
```
````
`````
```````

```{seealso}
See {ref}`concepts:aero-coefficients` for coefficient definitions, axis conventions, and how to recover dimensional forces and moments.
```

(quickstart:python-api)=
## Python API

% To update plots in this section: python examples/b737.py --docs

```{seealso}
- [examples/b737/b737.avl](https://github.com/brio50/avl-aero-tables/blob/master/examples/b737/b737.avl) — Boeing 737 geometry with wing, horizontal tail, and vertical tail
- [examples/b737/b737.yml](https://github.com/brio50/avl-aero-tables/blob/master/examples/b737/b737.yml) — project file driving the sweep below
- [examples/b737.py](https://github.com/brio50/avl-aero-tables/blob/master/examples/b737.py) — fully runnable version of this walkthrough (`--docs` flag)
```

### Read & Plot Geometry

`````{card}
:class-card: cli-card

```{code-block} python
:caption: Input
from avl_aero_tables import avl_fileread, avl_fileplot

geom = avl_fileread("examples/b737/b737.avl")

print(geom.header.name)          # 737-800 raised tail
print(list(geom.surface.keys())) # ['Wing', 'Stab', 'Fin', 'Fuselage_H', ...]
print(geom.ctrl_names)           # ['slat', 'flap', 'aileron', 'elevator', 'rudder']
print(geom.header.Sref)          # 1260.0  (reference area, sq-ft)

fig = avl_fileplot(geom)
fig.write_html("b737_geometry.html", include_plotlyjs="cdn")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

```{plotly-figure} _static/html/b737_geometry.html
```
`````

### Sweep Alpha / Beta

`out_dir` is a base directory — `avl_sweep` creates `_runs/b737_<timestamp>/` inside it automatically.  The completion message and debug log are written to `<run_dir>/<stem>.log` (where `<stem>` is the `.avl` filename without extension — e.g. `b737.log` for `b737.avl`); nothing is printed to the console unless you configure `logging` yourself.

`````{card}
:class-card: cli-card

```{code-block} python
:caption: Input
from pathlib import Path
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="examples/b737/b737.avl",
    alpha=list(range(-6, 13, 2)),   # -6 to +12 deg, 2 deg steps
    beta=[0.0],
    out_dir=Path("_runs"),
)

print(f"{len(results)} cases computed")
for r in results[:3]:
    print(f"  Alpha={r.data['Alpha']:5.1f}  CLtot={r.data['CLtot']:.4f}")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
10 cases computed
  Alpha= -6.0  CLtot=-0.4135
  Alpha= -4.0  CLtot=-0.2376
  Alpha= -2.0  CLtot=0.0362
```
`````

### Sweep Control Surfaces

`````{card}
:class-card: cli-card

```{code-block} python
:caption: Input
results = avl_sweep(
    avl_file="examples/b737/b737.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, -5.0, 0.0, 5.0, 10.0]},
    out_dir=Path("_runs"),
)
print(f"{len(results)} cases (4 alpha × 5 elevator deflections)")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
20 cases (4 alpha × 5 elevator deflections)
```
`````

```{seealso}
See {doc}`concepts` for how `ctrl_sweeps` counts cases and why `0.0` must be included for stability tables.
```

### Build Aero Database

`````{card}
:class-card: cli-card

```{code-block} python
:caption: Input
from avl_aero_tables import aero_filewrite

results = avl_sweep(
    avl_file="examples/b737/b737.avl",
    alpha=list(range(-5, 16, 5)),
    beta=list(range(-5, 6, 5)),
    ctrl_sweeps={
        "slat":     [0.0, 5.0, 10.0],
        "flap":     [0.0, 10.0, 20.0],
        "aileron":  [-10.0, 0.0, 10.0],
        "elevator": [-10.0, 0.0, 10.0],
        "rudder":   [-10.0, 0.0, 10.0],
    },
    out_dir=Path("_runs"),
)

aero = aero_filewrite(results)
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton
AeroDatabase: 5α × 3β  |  δ_slat = 3, δ_flap = 3, δ_aileron = 3, δ_elevator = 3, δ_rudder = 3
```
`````

### Plot Total Coefficients

```{admonition} Nonlinear 6-DOF table-lookup
:class: note
Total force and moment coefficients ($C_{L_\mathrm{total}}$, $C_{D_\mathrm{total}}$, $C_{m_\mathrm{total}}$, …) — the primary output for flight dynamics work. The "Stability" figure shows coefficients vs. $\alpha$ and $\beta$ at neutral controls; each subsequent figure shows one coefficient vs. $\alpha$ and $\delta$ for every control surface.
```

```````{card}
:class-card: cli-card full-width

```{code-block} python
:caption: Input
from avl_aero_tables import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
names = ["b737_total_stab", "b737_total_ctrl_lift", "b737_total_ctrl_side",
         "b737_total_ctrl_drag", "b737_total_ctrl_roll", "b737_total_ctrl_pitch",
         "b737_total_ctrl_yaw"]
for fig, name in zip(figs, names):
    fig.write_html(f"{name}.html", include_plotlyjs="cdn")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

`````{tab-set}
:class: aero-plots
````{tab-item} Stability
```{plotly-figure} _static/html/b737_total_stab.html
```
````
````{tab-item} CL
```{plotly-figure} _static/html/b737_total_ctrl_lift.html
```
````
````{tab-item} CY
```{plotly-figure} _static/html/b737_total_ctrl_side.html
```
````
````{tab-item} CD
```{plotly-figure} _static/html/b737_total_ctrl_drag.html
```
````
````{tab-item} Cl
```{plotly-figure} _static/html/b737_total_ctrl_roll.html
```
````
````{tab-item} Cm
```{plotly-figure} _static/html/b737_total_ctrl_pitch.html
```
````
````{tab-item} Cn
```{plotly-figure} _static/html/b737_total_ctrl_yaw.html
```
````
`````
```````

```{tip}
The control-surface figures show a **$\beta = 0°$ slice** of the full 3-D table ($\alpha \times \beta \times \delta$). To inspect off-zero sideslip, pass `beta_ref` — e.g. `aero_fileplot(aero, beta_ref=5.0)`.
```

### Plot Stability Derivatives

```{admonition} Linear analysis — stability derivatives, trim sensitivity, control law design
:class: note
Linearised $\partial C / \partial(\alpha, \beta, p', q', r')$ at neutral controls. One figure per perturbation variable, six subplots per figure ($C_L$, $C_Y$, $C_D$, $C_l$, $C_m$, $C_n$). Use for stability analysis and linear control law derivation — not as look-up coefficients in a nonlinear sim.
```

```````{card}
:class-card: cli-card full-width

```{code-block} python
:caption: Input
from avl_aero_tables import aero_stabderivplot

stab_figs = aero_stabderivplot(aero)
names = ["b737_deriv_stab_alpha", "b737_deriv_stab_beta",
         "b737_deriv_stab_p", "b737_deriv_stab_q", "b737_deriv_stab_r"]
for fig, name in zip(stab_figs, names):
    fig.write_html(f"{name}.html", include_plotlyjs="cdn")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

`````{tab-set}
:class: aero-plots
````{tab-item} ∂/∂α
```{plotly-figure} _static/html/b737_deriv_stab_alpha.html
```
````
````{tab-item} ∂/∂β
```{plotly-figure} _static/html/b737_deriv_stab_beta.html
```
````
````{tab-item} ∂/∂p'
```{plotly-figure} _static/html/b737_deriv_stab_p.html
```
````
````{tab-item} ∂/∂q'
```{plotly-figure} _static/html/b737_deriv_stab_q.html
```
````
````{tab-item} ∂/∂r'
```{plotly-figure} _static/html/b737_deriv_stab_r.html
```
````
`````
```````

### Plot Control Derivatives

```{admonition} Control effectiveness — surface sizing, linear autopilot design
:class: note
Linearised $\partial C / \partial\delta_\text{surface}$ at neutral controls. One figure per control surface, six subplots per figure ($C_L$, $C_Y$, $C_D$, $C_l$, $C_m$, $C_n$ vs. $\alpha$ and $\beta$). Use for control allocation, handling qualities assessment, and linear autopilot gain derivation.
```

```````{card}
:class-card: cli-card full-width

```{code-block} python
:caption: Input
from avl_aero_tables import aero_ctrlderivplot

ctrl_figs = aero_ctrlderivplot(aero)
surfaces = ["slat", "flap", "aileron", "elevator", "rudder"]
for fig, surface in zip(ctrl_figs, surfaces):
    fig.write_html(f"b737_deriv_ctrl_{surface}.html", include_plotlyjs="cdn")
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

`````{tab-set}
:class: aero-plots
````{tab-item} slat
```{plotly-figure} _static/html/b737_deriv_ctrl_slat.html
```
````
````{tab-item} flap
```{plotly-figure} _static/html/b737_deriv_ctrl_flap.html
```
````
````{tab-item} aileron
```{plotly-figure} _static/html/b737_deriv_ctrl_aileron.html
```
````
````{tab-item} elevator
```{plotly-figure} _static/html/b737_deriv_ctrl_elevator.html
```
````
````{tab-item} rudder
```{plotly-figure} _static/html/b737_deriv_ctrl_rudder.html
```
````
`````
```````

```{seealso}
See {ref}`concepts:aero-coefficients` for coefficient definitions, axis conventions, and how to recover dimensional forces and moments. See {ref}`concepts:output-types` for when to use totals vs. derivatives in simulation.
```
