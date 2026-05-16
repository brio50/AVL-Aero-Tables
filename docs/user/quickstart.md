# Quickstart

## Bubble Dancer Walkthrough

The Bubble Dancer (`examples/bd/`) is the canonical reference example — a sailplane with a fuselage body, four control surfaces (flap, aileron, elevator, rudder), and external airfoil coordinate files. Its directory structure is the recommended pattern for any custom geometry:

```{code-block} text
:class: no-copybutton
📁 examples/bd/
├── 📄 bd.avl          ← geometry: surfaces, sections, control hinges, reference quantities
├── 📄 fuseBD.dat      ← fuselage body cross-section coordinates (referenced by bd.avl)
├── 📄 ag35.dat        ← airfoil coordinates (referenced by bd.avl AFIL entries)
├── 📄 ag36.dat
└── 📄 ag37.dat
```

Keep all these files together. `avl_sweep` sets AVL's working directory to the folder containing the `.avl` file, so every relative path inside it (`fuseBD.dat`, `ag35.dat`, etc.) resolves automatically.

For your own project, keep geometry inputs versioned in git and runs outside of version control:

```{code-block} text
:class: no-copybutton
📁 my_project/          ← git repo
├── 📁 design_a/
│   ├── 📄 design_a.avl      ← geometry: surfaces, sections, control hinges
│   ├── 📄 wing_airfoil.dat  ← airfoil coordinates   (AFIL entry in .avl)
│   └── 📄 fuselage.dat      ← body cross-sections   (BFIL entry in .avl)
├── 📁 design_b/
│   ├── 📄 design_b.avl
│   └── 📄 wing_airfoil.dat
├── 📁 runs/                 ← generated at runtime; add to .gitignore
│   ├── 📁 design_a_2026-05-14-091234/
│   └── 📁 design_a_2026-05-15-143022/
├── 📄 .gitignore            ← contains: runs/
└── 📄 analysis.py
```

```{note}
A fully runnable version of this walkthrough is available as `examples/quickstart.py`.
Run it from anywhere with `python examples/quickstart.py` — outputs go to `examples/runs/bd_<timestamp>/`.
```

### Read & Plot Geometry

```python
from avl_aero_tables import avl_fileread, avl_fileplot

geom = avl_fileread("examples/bd/bd.avl")

print(geom.header.name)          # Bubble Dancer RES
print(list(geom.surface.keys())) # ['Wing', 'Horizontal_tail', 'Vertical_tail']
print(geom.header.Sref)          # 1000.0  (reference area, sq-in)

fig = avl_fileplot(geom)
fig.savefig("bd_geometry.png", dpi=150)
```

![Bubble Dancer four-view geometry plot](../_static/img/bd_geometry.png)

### Sweep Alpha / Beta

`out_dir` is a base directory — `avl_sweep` creates `runs/bd_<timestamp>/` inside it automatically:

```python
from pathlib import Path
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-6, 13, 2)),   # -6 to +12 deg, 2 deg steps
    beta=[0.0],
    out_dir=Path("runs"),
)

print(f"{len(results)} cases computed")
for r in results[:3]:
    print(f"  Alpha={r.data['Alpha']:5.1f}  CLtot={r.data['CLtot']:.4f}")
```

```
AVL sweep complete → /your/project/runs/bd_2026-05-15-143022  (10 cases)
10 cases computed
  Alpha= -6.0  CLtot=-0.1669
  Alpha= -4.0  CLtot=0.0311
  Alpha= -2.0  CLtot=0.2299
```

### Sweep Control Surfaces

```python
results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, -5.0, 0.0, 5.0, 10.0]},
    out_dir=Path("runs"),
)
print(f"{len(results)} cases (4 alpha × 5 elevator deflections)")
```

```
AVL sweep complete → /your/project/runs/bd_2026-05-15-143022  (20 cases)
20 cases (4 alpha × 5 elevator deflections)
```

```{seealso}
See {doc}`concepts` for how `ctrl_sweeps` counts cases and why `0.0` must be included for stability tables.
```

### Build Aero Database

```python
from avl_aero_tables import aero_filewrite

results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-5, 16, 5)),
    beta=list(range(-5, 6, 5)),
    ctrl_sweeps={
        "flap":     [-10.0, 0.0, 10.0],
        "aileron":  [-15.0, 0.0, 15.0],
        "elevator": [-20.0, 0.0, 20.0],
        "rudder":   [-20.0, 0.0, 20.0],
    },
    out_dir=Path("runs"),
)

aero = aero_filewrite(results)

print(aero.stab["CLtot"].data.shape)               # (5, 3) — alpha × beta
print(aero.ctrl["CLtot_d03_elevator"].data.shape)  # (5, 3, 3) — alpha × beta × defl
```

### Plot Aero Coefficients

```python
from avl_aero_tables import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
names = ["bd_stab", "bd_ctrl_CLtot", "bd_ctrl_CYtot",
         "bd_ctrl_CDtot", "bd_ctrl_Cltot", "bd_ctrl_Cmtot", "bd_ctrl_Cntot"]
for fig, name in zip(figs, names):
    fig.savefig(f"{name}.png", dpi=150)
```

````{tab-set}
```{tab-item} Stability
![Bubble Dancer stability derivatives](../_static/img/bd_stab.png)
```
```{tab-item} CL
![CLtot control derivatives](../_static/img/bd_ctrl_CLtot.png)
```
```{tab-item} CY
![CYtot control derivatives](../_static/img/bd_ctrl_CYtot.png)
```
```{tab-item} CD
![CDtot control derivatives](../_static/img/bd_ctrl_CDtot.png)
```
```{tab-item} Cl
![Cltot control derivatives](../_static/img/bd_ctrl_Cltot.png)
```
```{tab-item} Cm
![Cmtot control derivatives](../_static/img/bd_ctrl_Cmtot.png)
```
```{tab-item} Cn
![Cntot control derivatives](../_static/img/bd_ctrl_Cntot.png)
```
````
