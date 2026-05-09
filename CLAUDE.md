# CLAUDE.md — Project Context for AI Assistants

## What this project is

A Python package (`avl_wrapper`) that wraps [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT).  It drives AVL via stdin command scripts, parses its output, and returns structured Python data.

---

## File structure

```
avl_wrapper/          # Python package
  __init__.py         # public API
  avl_fileread.py     # parse .avl geometry files → AvlGeometry dataclass
  st_fileread.py      # parse .st stability output files → list[StResult]
  avl_rungen.py       # generate AVL run-case and command file strings
  avl_bin.py          # find/verify/invoke the AVL binary; CLI entry point
  avl_aerogen.py      # top-level sweep orchestration → list[StResult]
  avl_fileplot.py     # four-view geometry plot → Figure
  aero_filewrite.py   # pivot list[StResult] → AeroDatabase (numpy tables)
  aero_fileplot.py    # 3-D surface plots of AeroDatabase tables

examples/             # AVL geometry + run files (bd.avl, supra.avl, etc.)
docs/                 # AVL user documentation
out/                  # AVL .st output files (generated at runtime, not committed)
tests/
  data/               # hand-generated .st data files for unit testing
  test_avl_fileread.py
  test_st_fileread.py
  test_avl_rungen.py
  test_avl.py
  test_avl_aerogen.py
  test_avl_fileplot.py
  test_aero_filewrite.py
  test_aero_fileplot.py
```

---

## Operation flow

```
User code / CLI
    │
    ▼
avl_aerogen.run(avl_file, alpha, beta, ctrl_sweeps, out_dir)
    │
    ├─ avl_fileread(avl_file)          → AvlGeometry (header, surfaces, body)
    │   └─ extracts control surface names (ctrl_names, ordered)
    │
    ├─ avl_rungen.make_command(...)    → AVL command script string
    │   └─ LOAD <name> / PLOP G / OPER / per-case: A,B,Di, i, x, st, CINI / Quit
    │
    ├─ avl_bin.run(cmd_text, cwd=avl_dir)  → subprocess driving AVL binary via stdin
    │   └─ .st files written to a short /tmp staging dir (AVL ~80-char path limit)
    │   └─ .st files moved to out_dir after AVL exits
    │
    └─ st_fileread(out_dir)            → list[StResult]
        └─ each StResult has .filename, .controls, .data (dict of floats)
```

---

## Key design decisions

- **Numeric case filenames** (`case_0001.st`): AVL's Fortran source has an ~80-char
  string limit for output filenames.  Descriptive names were hitting this limit.
  All flight condition data (Alpha, Beta, control deflections) is inside the .st
  file itself, so numeric names lose no information.

- **Staging in /tmp**: `avl_aerogen.run()` writes .st files to a short
  `tempfile.TemporaryDirectory(prefix="avl_")` path to stay under the 80-char
  limit, then moves them to the caller's `out_dir`.

- **cwd = avl_dir**: AVL is invoked with `cwd` set to the directory containing
  the .avl file so that `LOAD <name>` resolves without a path.

- **`make_command` loop structure**: when `ctrl_sweeps` is empty, one run is
  emitted per `(alpha, beta)` point.  When `ctrl_sweeps` has entries, surfaces
  are swept independently (not combinatorially) — matching the MATLAB behavior.

- **`Clb_Cnr_div_Clr_Cnb` key in StResult**: the `.st` line `Clb Cnr / Clr Cnb = <value>` is stored under that compound key (5-token lookback) to avoid overwriting the real `Cnb` stability derivative.

- **BODY/SURFACE parsing**: BODY is a standalone `if`; after its inner while loop exits on the next SURFACE line, the SURFACE `if` block fires in the same outer iteration (sequential `if`, not `elif`).

- **Stability tables only filled for neutral-control runs**: `aero_filewrite` checks `all_neutral = all(abs(r.data.get(name, 0.0)) < 1e-6 for name in ctrl_map.values())` before populating `stab` tables, so off-neutral sweeps don't corrupt the neutral aero map.

---

## Future work

- **scipy interpolation**: add `scipy.interpolate.RegularGridInterpolator` support to
  `AeroDatabase` so users can query coefficients at arbitrary (alpha, beta, defl) points
  between breakpoints, not just at exact breakpoint values.  The numpy arrays in
  `StabTable` and `CtrlTable` are already shaped correctly for `RegularGridInterpolator`.
  Expose as an `interpolate(coef, alpha, beta, defl=0.0)` method or standalone helper.

---

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Run tests:

```bash
.venv/bin/pytest           # all tests
.venv/bin/pytest -k avl_fileread   # one module
```

The AVL binary must be installed at `~/bin/avl` (see README.md for build
instructions).  Integration tests are skipped automatically if the binary is
absent.

