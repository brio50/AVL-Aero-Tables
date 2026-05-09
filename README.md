# Python AVL Wrapper

![Tests](https://github.com/brio50/Matlab-AVL-Wrapper/actions/workflows/test.yml/badge.svg)

A Python wrapper for [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT). Drives AVL via stdin command scripts, parses its `.st` output, and returns structured Python data — no manual file editing required.

---

## Requirements

- Python 3.9+
- AVL 3.52 binary installed at `~/bin/avl` (see below)

---

## 1. Install AVL

AVL is a Fortran program distributed as source by MIT. Build it yourself and place the binary at `~/bin/avl`.

### macOS

```bash
brew install --cask xquartz   # X11 (required for AVL graphics mode)
brew install gcc               # provides gfortran
mkdir -p ~/bin
ln -sf /opt/homebrew/Cellar/gcc/15.2.0_1/bin/gfortran-15 ~/bin/gfortran
export PATH="$HOME/bin:$PATH"  # add to ~/.zshrc
```

Download `avl3.52.tgz` from https://web.mit.edu/drela/Public/web/avl/, extract, then:

```bash
cd AVL3.52rel09032025
cd eispack && make -f Makefile.gfortran FC=~/bin/gfortran && cd ..
cd plotlib && cp config.make.gfortranDP config.make && make gfortranDP FC=~/bin/gfortran CC=/usr/bin/cc && cd ..
cd bin && make -f Makefile.gfortranDP FC=~/bin/gfortran
cp avl ~/bin/avl
```

### Linux

```bash
sudo apt install gfortran libx11-dev   # Debian/Ubuntu
# sudo dnf install gcc-gfortran libX11-devel  # Fedora/RHEL
# Then follow the same build steps above
```

### Windows

A pre-built binary is on the [AVL download page](https://web.mit.edu/drela/Public/web/avl/). Place it on your `PATH`.

### Verify

```bash
avl-wrapper verify
# AVL 3.52 found at /Users/you/bin/avl — OK
```

---

## 2. Install the package

```bash
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

pip install -e ".[dev]"        # editable install with dev extras
```

---

## 3. Pipeline overview

The wrapper follows the same sequential pipeline as the original MATLAB implementation:

```
avl_fileread()      →  read and parse .avl geometry
avl_fileplot()      →  plot geometry (four views)
avl()               →  run AVL sweep, collect .st results
aero_filewrite()    →  pivot results into lookup tables
aero_fileplot()     →  plot the aero database
```

`avl()` is the primary entry point. It reads the geometry, builds the AVL
command script, runs the binary, and returns parsed results — all in one call.

---

## 4. End-to-end example: Bubble Dancer (`bd.avl`)

`bd.avl` is a sailplane with four control surfaces — flap, aileron, elevator,
and rudder. This walkthrough follows the pipeline from geometry through
a full aero database.

### 4a. Read and plot the geometry

```python
from avl_wrapper import avl_fileread, avl_fileplot

geom = avl_fileread("examples/bd.avl")

print(geom.header.name)          # Bubble Dancer RES
print(list(geom.surface.keys())) # ['Wing', 'Horizontal_tail', 'Vertical_tail']
print(geom.header.Sref)          # 1000.0  (reference area, sq-in)

fig = avl_fileplot(geom)         # four-view geometry plot
fig.savefig("bd_geometry.png", dpi=150)
```

### 4b. Run an alpha / beta sweep

```python
from avl_wrapper import avl

results = avl(
    avl_file="examples/bd.avl",
    alpha=list(range(-6, 13, 2)),   # -6 to +12 deg, 2 deg steps
    beta=[0.0],                     # zero sideslip
)

print(f"{len(results)} cases computed")
for r in results[:3]:
    print(f"  Alpha={r.data['Alpha']:5.1f}  CLtot={r.data['CLtot']:.4f}")
```

Sample output:
```
10 cases computed
  Alpha= -6.0  CLtot=-0.1669
  Alpha= -4.0  CLtot=0.0311
  Alpha= -2.0  CLtot=0.2299
```

### 4c. Sweep control surfaces

Pass `ctrl_sweeps` to sweep one or more control surfaces. Control surface
names come from the `CONTROL` entries in the `.avl` file — `avl()` extracts
them automatically. Typical deflection range: −5 to +5 deg.

```python
results = avl(
    avl_file="examples/bd.avl",
    alpha=[-4.0, 0.0, 4.0, 8.0],
    beta=[0.0],
    ctrl_sweeps={"elevator": [-10.0, -5.0, 0.0, 5.0, 10.0]},
)
print(f"{len(results)} cases (4 alpha × 5 elevator deflections)")
```

### 4d. Build an aero database

```python
from avl_wrapper import aero_filewrite

# Run a full sweep: alpha × beta × elevator
results = avl(
    avl_file="examples/bd.avl",
    alpha=list(range(-6, 13, 2)),
    beta=[-6.0, -3.0, 0.0, 3.0, 6.0],
    ctrl_sweeps={"elevator": [-10.0, 0.0, 10.0]},
)

aero = aero_filewrite(results)

print(aero.stab["CLtot"].data.shape)               # (10, 5) — alpha × beta
print(aero.ctrl["CLtot_d03_elevator"].data.shape)  # (10, 5, 3) — alpha × beta × defl
```

Stability tables (`aero.stab`) are populated only for neutral-control runs
(all deflections = 0). Control tables (`aero.ctrl`) cover all runs.

### 4d-ii. Export results to a file

Use `results_to_dataframe()` to convert results to a pandas DataFrame for
saving to any tabular format:

```python
from avl_wrapper import results_to_dataframe

df = results_to_dataframe(results)

df.to_csv("sweep.csv", index=False)          # CSV
df.to_hdf("sweep.h5", key="results")         # HDF5
df.to_parquet("sweep.parquet")               # Parquet
df.to_json("sweep.json", orient="records")   # JSON
```

The DataFrame has one row per run case. Columns include `filename`, `Alpha`,
`Beta`, all stability derivatives, all control derivatives, and control surface
deflections.

### 4e. Plot the aero database

```python
from avl_wrapper import aero_fileplot

figs = aero_fileplot(aero, beta_ref=0.0)
figs[0].savefig("bd_stab_coefs.png", dpi=150)   # stability surface plots
figs[1].savefig("bd_ctrl_CLtot.png", dpi=150)   # CLtot vs elevator at beta=0
```

---

## CLI

```bash
# Verify AVL binary is installed and working
avl-wrapper verify

# Feed a hand-written command file directly to AVL
avl-wrapper run my_commands.txt
```

---

## API reference

| Symbol | Description |
|---|---|
| `avl(avl_file, alpha, beta, ctrl_sweeps, out_dir)` | Run AVL sweep → `list[StResult]` — primary entry point |
| `avl_fileread(path)` | Parse `.avl` geometry → `AvlGeometry` |
| `avl_fileplot(geom)` | Four-view geometry plot → `Figure` |
| `aero_filewrite(results)` | Pivot results → `AeroDatabase` lookup tables |
| `aero_fileplot(aero, beta_ref)` | Plot `AeroDatabase` → `list[Figure]` |
| `st_fileread(path)` | Parse `.st` files from a directory → `list[StResult]` |
| `results_to_dataframe(results)` | Convert `list[StResult]` → `pd.DataFrame` for CSV / HDF5 / Parquet export |

---

## References

- AVL homepage: https://web.mit.edu/drela/Public/web/avl/
- AVL user guide: [`docs/avl_doc.txt`](docs/avl_doc.txt)
