# Quickstart

## Bubble Dancer walkthrough

The Bubble Dancer (`examples/bd/`) is the canonical reference example — a sailplane with a fuselage body, four control surfaces (flap, aileron, elevator, rudder), external airfoil coordinate files, and a mass/inertia file. Its directory structure is the recommended pattern for any custom geometry:

```{code-block} text
:class: no-copybutton
📁 examples/bd/
├── 📄 bd.avl          ← geometry: surfaces, sections, control hinges, reference quantities
├── 📄 bd.mass         ← mass & inertia: CG location, mass, Ixx/Iyy/Izz
├── 📄 fuseBD.dat      ← fuselage body cross-section coordinates (referenced by bd.avl)
├── 📄 ag35.dat        ← airfoil coordinates (referenced by bd.avl AFIL entries)
├── 📄 ag36.dat
└── 📄 ag37.dat
```

Keep all these files together. `avl_sweep` sets AVL's working directory to the folder containing the `.avl` file, so every relative path inside it (`fuseBD.dat`, `ag35.dat`, etc.) resolves automatically.

### Read and plot the geometry

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

### Run an alpha / beta sweep

```python
from avl_aero_tables import avl_sweep

results = avl_sweep(
    avl_file="examples/bd/bd.avl",
    alpha=list(range(-6, 13, 2)),   # -6 to +12 deg, 2 deg steps
    beta=[0.0],
    mass_file="bd.mass",            # bare filename → resolves to examples/bd/bd.mass
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
    avl_file="examples/bd/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, -5.0, 0.0, 5.0, 10.0]},
)
print(f"{len(results)} cases (4 alpha × 5 elevator deflections)")
```

```
AVL sweep complete → /your/project/out/bd/2026-05-15-143022  (20 cases)
20 cases (4 alpha × 5 elevator deflections)
```

See {doc}`../concepts` for how `ctrl_sweeps` counts cases and why `0.0` must be included for stability tables.

### Build an aero database

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
    mass_file="bd.mass",
)

aero = aero_filewrite(results)

print(aero.stab["CLtot"].data.shape)               # (5, 3) — alpha × beta
print(aero.ctrl["CLtot_d03_elevator"].data.shape)  # (5, 3, 3) — alpha × beta × defl
```

### Plot the aero database

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
