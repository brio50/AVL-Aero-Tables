# CLAUDE.md — Project Context for AI Assistants

## What this project is

A Python package (`avl_aero_tables`) that wraps [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT).  It drives AVL via stdin command scripts, parses its output, and returns structured Python data.

---

## File structure

```
avl_aero_tables/          # Python package
  __init__.py         # public API
  avl_fileread.py     # parse .avl geometry files → AvlGeometry dataclass
  st_fileread.py      # parse .st stability output files → list[StResult]
  avl_rungen.py       # generate AVL run-case and command file strings
  avl_bin.py          # find/verify/invoke the AVL binary; CLI entry point
  avl_sweep.py        # top-level sweep orchestration → list[StResult]
  avl_fileplot.py     # four-view geometry plot → Figure
  aero_filewrite.py   # pivot list[StResult] → AeroDatabase (numpy tables)
  aero_fileplot.py    # 3-D surface plots of AeroDatabase tables

examples/             # AVL geometry + run files (bd.avl, supra.avl, etc.)
docs/                 # AVL user documentation
out/                  # sweep outputs (generated at runtime, not committed)
                      #   out/<name>/YYYY-MM-DD-HHMMSS/  — one subdir per run
tests/
  data/               # hand-generated .st data files for unit testing
  test_avl_fileread.py
  test_st_fileread.py
  test_avl_rungen.py
  test_avl.py
  test_avl_aerogen.py  # (tests avl_sweep.py)
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
avl_sweep.run(avl_file, alpha, beta, ctrl_sweeps, out_dir, binary, out_format, mass_file)
    │
    ├─ avl_fileread(avl_file)              → AvlGeometry (header, surfaces, body)
    │   └─ extracts control surface names (ctrl_names, ordered)
    │
    ├─ avl_rungen.make_run_reset(...)      → reset.run  (written to staging + out_dir)
    │   └─ AVL native .run format; all flight conditions zeroed
    │   └─ staging copy passed as CLI arg (short /tmp path stays under 80-char limit)
    │
    ├─ avl_rungen.make_run_command(...)    → cmd_text (fed to AVL stdin via staging paths)
    │   └─ called twice: once with staging paths (→ cmd_text), once with out_dir paths (→ sweep.log)
    │   └─ PLOP G / OPER / per-case: A,B,Di, i, x, st, CINI / Quit  (no LOAD)
    │
    ├─ avl_bin.run(cmd_text, avl_file, run_file, [mass_file], cwd=avl_dir)
    │   └─ subprocess: avl <avl_file.name> <staging/reset.run> [<mass>] + stdin
    │   └─ .st files written to short /tmp staging dir; moved to out_dir after AVL exits
    │
    ├─ st_fileread(out_dir)                → list[StResult]
    │   └─ each StResult has .filename, .controls, .data (dict of floats)
    │
    └─ results_to_dataframe(results)       → DataFrame → results.csv / results.json
        └─ skipped when out_format == "df"
```

---

## Key design decisions

- **Numeric case filenames** (`case_0001.st`): AVL's Fortran source has an ~80-char
  string limit for output filenames.  Descriptive names were hitting this limit.
  All flight condition data (Alpha, Beta, control deflections) is inside the .st
  file itself, so numeric names lose no information.

- **AVL CLI interface**: AVL is invoked as `avl <avl_file> <reset.run> [<mass_file>]`
  with the sweep commands piped to stdin — matching AVL's documented CLI interface
  and the original MATLAB implementation.  This is why `reset.run` is a real input
  and why no `LOAD` or `MASS` commands appear in the stdin script.

- **File-based AVL inputs**: `avl_sweep.run()` writes `reset.run` and `sweep.log`
  to `out_dir` so the full inputs are on disk alongside the outputs.  `sweep.log`
  opens with a `#` comment line containing the exact shell command to replay the run.

- **Two command strings**: `make_run_command` is called twice — once with
  `out_dir` paths (written to `sweep.log` for human reference) and once with
  `/tmp` staging paths (fed to AVL stdin to stay under the 80-char Fortran limit).

- **Staging in /tmp**: AVL writes `.st` files — and `reset.run` is staged — in a
  short `tempfile.TemporaryDirectory(prefix="avl_")` path to keep all AVL-facing
  filenames under the ~80-char Fortran string limit.  Files are moved to `out_dir`
  after AVL exits; the temp directory is deleted automatically even if AVL crashes.

- **cwd = avl_dir**: AVL is invoked with `cwd` set to the directory containing
  the `.avl` file so that bare filenames (geometry, mass) resolve correctly, and
  relative paths inside the `.avl` file (airfoil data, etc.) also resolve.
- **`make_run_command` loop structure**: when `ctrl_sweeps` is empty, one run is
  emitted per `(alpha, beta)` point.  When `ctrl_sweeps` has entries, surfaces
  are swept independently (not combinatorially) — matching the MATLAB behavior.

- **`Clb_Cnr_div_Clr_Cnb` key in StResult**: the `.st` line `Clb Cnr / Clr Cnb = <value>` is stored under that compound key (5-token lookback) to avoid overwriting the real `Cnb` stability derivative.

- **BODY/SURFACE parsing**: BODY is a standalone `if`; after its inner while loop exits on the next SURFACE line, the SURFACE `if` block fires in the same outer iteration (sequential `if`, not `elif`).

- **Stability tables only filled for neutral-control runs**: `aero_filewrite` checks `all_neutral = all(abs(r.data.get(name, 0.0)) < 1e-6 for name in ctrl_map.values())` before populating `stab` tables, so off-neutral sweeps don't corrupt the neutral aero map.

---

## Version source of truth

The single source of truth for the package version is `pyproject.toml` → `[project] version`.

- `docs/conf.py` reads it at build time via `importlib.metadata.version("avl-aero-tables")`
- The installed package name is `avl-aero-tables` (not `python-avl-wrapper`, which was the old name — uninstall the old one if both appear in `pip list`)
- When investigating version mismatches, check `pip list | grep avl` for stale editable installs from the pre-rename era

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

---

## PR workflow

Before opening a pull request, run these in order:

```bash
# 1. Auto-fix and format
.venv/bin/ruff check --fix avl_aero_tables/ tests/
.venv/bin/ruff format avl_aero_tables/ tests/

# 2. Full test suite
.venv/bin/pytest
```

Remaining `ruff` violations after `--fix` are either `E501` (long lines — wrap
manually) or `F821` false positives on quoted forward-reference annotations
(`"matplotlib.figure.Figure"`, `"pd.DataFrame"`); the latter are intentional
and should be left alone.

