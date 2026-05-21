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

Keep all these files together. AVL's working directory is set to the folder containing the `.avl` file, so every relative path inside it (`fuseBD.dat`, `ag35.dat`, etc.) resolves automatically.

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
AVL sweep complete → _runs/bd/2026-05-15-143022  (45 cases)
```
`````

```{note}
Results land in `_runs/<yml-stem>/<timestamp>/` relative to the **project root** — one directory up from the `.yml` file. This differs from the Python API, where you control `out_dir` directly.
```

### Plot Results

Pass a parent directory to plot the latest sweep, or a specific timestamped directory to plot a particular run.

```````{card}
:class-card: cli-card full-width

```{code-block} console
:caption: Input
$ avl-aero-tables plot aero _runs/bd/
```
^^^
```{code-block} text
:caption: Output
:class: no-copybutton hide-empty-codeblock
```

`````{tab-set}
:class: aero-plots
````{tab-item} Stability
```{plotly-figure} _static/html/bd_stab.html
```
````
````{tab-item} CL
```{plotly-figure} _static/html/bd_ctrl_CLtot.html
```
````
````{tab-item} CY
```{plotly-figure} _static/html/bd_ctrl_CYtot.html
```
````
````{tab-item} CD
```{plotly-figure} _static/html/bd_ctrl_CDtot.html
```
````
````{tab-item} Cl
```{plotly-figure} _static/html/bd_ctrl_Cltot.html
```
````
````{tab-item} Cm
```{plotly-figure} _static/html/bd_ctrl_Cmtot.html
```
````
````{tab-item} Cn
```{plotly-figure} _static/html/bd_ctrl_Cntot.html
```
````
`````
```````

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

`out_dir` is a base directory — `avl_sweep` creates `_runs/bd_<timestamp>/` inside it automatically:

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
AVL sweep complete → /your/project/_runs/b737_2026-05-16-101818  (10 cases)
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
AVL sweep complete → /your/project/_runs/b737_2026-05-16-143022  (20 cases)
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

### Plot Aero Coefficients

```````{card}
:class-card: cli-card full-width

```{code-block} python
:caption: Input
from avl_aero_tables import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
names = ["b737_stab", "b737_ctrl_CLtot", "b737_ctrl_CYtot",
         "b737_ctrl_CDtot", "b737_ctrl_Cltot", "b737_ctrl_Cmtot", "b737_ctrl_Cntot"]
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
```{plotly-figure} _static/html/b737_stab.html
```
````
````{tab-item} CL
```{plotly-figure} _static/html/b737_ctrl_CLtot.html
```
````
````{tab-item} CY
```{plotly-figure} _static/html/b737_ctrl_CYtot.html
```
````
````{tab-item} CD
```{plotly-figure} _static/html/b737_ctrl_CDtot.html
```
````
````{tab-item} Cl
```{plotly-figure} _static/html/b737_ctrl_Cltot.html
```
````
````{tab-item} Cm
```{plotly-figure} _static/html/b737_ctrl_Cmtot.html
```
````
````{tab-item} Cn
```{plotly-figure} _static/html/b737_ctrl_Cntot.html
```
````
`````
```````
