# CLAUDE.md — Project Context for AI Assistants

## What this project is

A Python package (`avl_aero_tables`) that wraps [AVL](https://web.mit.edu/drela/Public/web/avl/) (Athena Vortex Lattice) by Mark Drela and Harold Youngren (MIT).  It drives AVL via stdin command scripts, parses its output, and returns structured Python data.

---

## File structure

```
avl_aero_tables/          # Python package
  __init__.py         # public API
  avl_fileread.py     # parse .avl geometry → AvlGeometry; parse .st output → list[StResult]
  avl_rungen.py       # generate AVL run-case and command file strings
  avl_bin.py          # find/verify/invoke the AVL binary; CLI entry point
  avl_sweep.py        # top-level sweep orchestration → list[StResult]
  avl_fileplot.py     # four-view geometry plot → Figure
  aero_filewrite.py   # pivot list[StResult] → AeroDatabase (numpy tables)
  aero_fileplot.py    # 3-D surface plots of AeroDatabase tables

docs/                 # AVL user documentation
examples/             # runnable scripts + Bubble Dancer reference geometry
  quickstart.py       # end-to-end walkthrough (geometry → sweep → plots)
  bd/                 # Bubble Dancer .avl, airfoil .dat, and bd_alpha5_beta0.st
_runs/                # sweep outputs (generated at runtime, not committed)
                      #   API:  <out_dir>/<avl-stem>_YYYY-MM-DD-HHMMSS/
                      #   CLI:  <project-root>/_runs/<avl-stem>/<avl-stem>_YYYY-MM-DD-HHMMSS/
tests/
  data/               # AVL geometry fixtures for unit testing (supra, allegro, etc.)
                      #   data/supra/, data/ellipg/, data/allegro/, data/b737/, etc.
  test_avl_fileread.py
  test_st_fileread.py  # tests st_fileread() from avl_fileread.py
  test_avl_rungen.py
  test_avl.py
  test_avl_aerogen.py  # (tests avl_sweep.py)
  test_avl_cli.py
  test_avl_fileplot.py
  test_aero_filewrite.py
  test_aero_fileplot.py
  test_integration.py  # end-to-end CLI + Python API against real AVL binary
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
    ├─ avl_rungen.make_run_reset(...)      → content string  (avl_sweep writes to staging + .in/reset.run)
    │   └─ AVL native .run format; all flight conditions zeroed
    │
    ├─ avl_rungen.make_run_command(...)    → cmd_text (fed to AVL stdin via staging paths)
    │   └─ called twice: once with staging paths (→ cmd_text), once with raw_dir + .in/ paths (→ .in/sweep.inp)
    │   └─ LOAD <avl_file> / CASE <reset.run> / PLOP G / OPER / per-case: A,B,Di, i, x, st, CINI / Quit
    │
    ├─ avl_bin.run(cmd_text, cwd=avl_dir)
    │   └─ subprocess: avl (no CLI args) + complete stdin script
    │   └─ .st files written to short /tmp staging dir; moved to .raw/ after AVL exits
    │
    ├─ st_fileread(run_dir/.raw)            → list[StResult]
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

- **Pure stdin interface**: AVL is an interactive Fortran program with no CLI argument
  for sweep commands.  `avl_bin.run()` invokes `avl` with no positional args and pipes
  the complete command script to stdin — matching the original MATLAB implementation
  (`avl < command.txt`).  The script opens with `LOAD <avl_file>` and `CASE <reset.run>`
  then proceeds to `PLOP G` / `OPER` / sweep loop / `Quit`.

- **File-based AVL inputs**: `avl_sweep.run()` writes `.in/reset.run` and `.in/sweep.inp`
  to the run directory so the full inputs are on disk alongside the outputs.  `sweep.inp`
  contains the complete stdin script (including `LOAD`/`CASE`) and is a record of
  exactly what was piped to AVL — not a runnable replay script (paths use actual
  `.raw/` and `.in/` dirs, which may exceed AVL's ~80-char Fortran limit).

- **Two command strings**: `make_run_command` is called twice — once with
  `raw_dir` + `.in/` paths (result written to `.in/sweep.inp` for human reference)
  and once with `/tmp` staging paths (fed to AVL stdin to stay under the 80-char Fortran limit).

- **Staging in /tmp**: AVL writes `.st` files in a short
  `tempfile.TemporaryDirectory(prefix="avl_")` path to keep all AVL-facing
  filenames under the ~80-char Fortran string limit.  Files are moved to `.raw/`
  after AVL exits; the temp directory is deleted automatically even if AVL crashes.

- **cwd = avl_dir**: AVL is invoked with `cwd` set to the directory containing
  the `.avl` file so that the bare filename in `LOAD` resolves correctly, and
  relative paths inside the `.avl` file (airfoil data, etc.) also resolve.
- **`make_run_command` loop structure**: when `ctrl_sweeps` is empty, one run is
  emitted per `(alpha, beta)` point.  When `ctrl_sweeps` has entries, surfaces
  are swept independently (not combinatorially) — matching the MATLAB behavior.

- **`Clb_Cnr_div_Clr_Cnb` key in StResult**: the `.st` line `Clb Cnr / Clr Cnb = <value>` is stored under that compound key (5-token lookback) to avoid overwriting the real `Cnb` stability derivative.

- **BODY/SURFACE parsing**: BODY is a standalone `if`; after its inner while loop exits on the next SURFACE line, the SURFACE `if` block fires in the same outer iteration (sequential `if`, not `elif`).

- **Stability tables only filled for neutral-control runs**: `aero_filewrite` checks `all_neutral = all(abs(r.data.get(name, 0.0)) < 1e-6 for name in ctrl_map.values())` before populating `stab` tables, so off-neutral sweeps don't corrupt the neutral aero map.

- **0.0 auto-injected into `ctrl_sweeps`**: if any surface's deflection list omits 0.0, `avl_sweep.run()` (and the YAML `SweepSpec` validator in `avl_config.py`) emits a `UserWarning` and inserts 0.0 — sorted into the list — so `db.stab` is always populated.  The original user-supplied list is never modified in place; a new dict is returned.

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

