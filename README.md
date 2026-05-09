# python-avl-wrapper

A Python wrapper for [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT). Generates aerodynamic coefficient tables for any `.avl` geometry file via alpha, beta, and control surface deflection sweeps.

## Requirements

- Python 3.10+
- AVL 3.52 binary installed at `~/bin/avl`
- [XQuartz](https://www.xquartz.org) (macOS only — required by AVL for X11 graphics)

---

## 1. Install AVL

AVL is a Fortran program distributed as source by MIT. You must build it yourself and place the binary in `~/bin/avl`.

### macOS (Apple Silicon or Intel)

**Prerequisites:**

```bash
brew install --cask xquartz   # X11 windowing (required for AVL graphics)
brew install gcc               # provides gfortran-15
```

Create a `gfortran` symlink in `~/bin` (substitute your GCC version if different):

```bash
mkdir -p ~/bin
ln -sf /opt/homebrew/Cellar/gcc/15.2.0_1/bin/gfortran-15 ~/bin/gfortran
```

Make sure `~/bin` is on your PATH (add to `~/.zshrc` if needed):

```bash
export PATH="$HOME/bin:$PATH"
```

**Build from source** (AVL 3.52, released 09/03/2025):

Download `avl3.52.tgz` from https://web.mit.edu/drela/Public/web/avl/ and extract it, then:

```bash
cd AVL3.52rel09032025

# 1. Build EISPACK linear algebra library
cd eispack
make -f Makefile.gfortran FC=~/bin/gfortran
cd ..

# 2. Build Xplot11 graphics library
cd plotlib
cp config.make.gfortranDP config.make
make gfortranDP FC=~/bin/gfortran CC=/usr/bin/cc
cd ..

# 3. Build AVL
cd bin
make -f Makefile.gfortranDP FC=~/bin/gfortran

# 4. Install to ~/bin
cp avl ~/bin/avl
```

**Verify:**

```bash
~/bin/avl
# AVL banner should appear — type 'quit' to exit
```

### Linux

Install prerequisites via your package manager, then follow the same build steps above:

```bash
sudo apt install gfortran libx11-dev   # Debian/Ubuntu
# or
sudo dnf install gcc-gfortran libX11-devel  # Fedora/RHEL
```

### Windows

A pre-built executable is available on the [AVL download page](https://web.mit.edu/drela/Public/web/avl/). Place it somewhere on your `PATH`.

---

## 2. Set up Python environment

```bash
# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows

# Install python-avl-wrapper
pip install python-avl-wrapper

# Or install in editable mode from source
pip install -e .
```

---

## 3. Quick start

```python
from avl_wrapper import sweep

results = sweep.run(
    avl_file="examples/bd.avl",
    alpha=range(-6, 13),
    beta=[-6, 0, 6],
)
results.plot()
```

---

## References

- AVL homepage: https://web.mit.edu/drela/Public/web/avl/
- AVL user guide: [`docs/avl_doc.txt`](docs/avl_doc.txt)
