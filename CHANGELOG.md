
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-09

### Added
- Full Python port of all eight MATLAB modules: `avl_fileread`, `st_fileread`, `avl_rungen`, `avl_bin`, `avl_aerogen`, `avl_fileplot`, `aero_filewrite`, `aero_fileplot`
- `avl()` as the primary public entry point (mirrors MATLAB `avl()` workflow)
- `avl_fileread` / `avl_fileplot`: parse `.avl` geometry files into `AvlGeometry` dataclass; four-view matplotlib plot
- `st_fileread`: parse AVL `.st` stability output files into `list[StResult]`; fixes `Clb Cnr / Clr Cnb` compound-key bug from MATLAB
- `avl_aerogen.run`: orchestrate full alpha/beta/ctrl sweep via AVL binary; stages `.st` files in `/tmp` to stay under AVL's 80-char filename limit
- `aero_filewrite`: pivot `list[StResult]` into `AeroDatabase` numpy lookup tables (alpha × beta for stability; alpha × beta × deflection for control)
- `aero_fileplot`: 3-D surface plots of stability and control coefficient tables
- `avl-wrapper` CLI with `verify` and `run` subcommands
- pytest suite: 150 tests covering all modules (unit + integration)
- GitHub Actions CI workflow (`.github/workflows/test.yml`); integration tests skip automatically when AVL binary is absent
- `pyproject.toml` using setuptools; installable via `pip install -e ".[dev]"`
- End-to-end `README.md` walkthrough using `bd.avl` (Bubble Dancer sailplane)

### Changed
- `avl_wrapper/avl.py` renamed to `avl_wrapper/avl_bin.py` so the `avl` name in the public namespace unambiguously refers to the sweep entry point
- `aero_filewrite` stability tables now populated only for neutral-control runs (all deflections = 0); fixes known MATLAB bug (was a TODO comment in `aero_filewrite.m`)
- `aero_fileplot` beta-index lookup generalised from hardcoded `CLtot_d1_flap` to `np.argmin` over any available beta breakpoints
- Pipeline overview added to README; section numbering updated

### Removed
- MATLAB source files (`.m`) removed from working tree; original sources preserved at git tag `v0.0.0-matlab`
- `avl_gui.m` not ported (MATLAB GUI Layout Toolbox; no Python equivalent needed)
- `examples/avl.exe` Windows PE32 binary (not applicable on macOS/Linux)
- `tmp/` directory (MATLAB command file holdover; now generated in-memory via `tempfile`)

## [0.0.0] - 2014-08-28

### Notes
- Initial MATLAB-based implementation; see tag `v0.0.0-matlab`
- Modules: `avl.m`, `avl_fileread.m`, `avl_fileplot.m`, `avl_rungen.m`,
  `st_fileread.m`, `avl_aerogen.m`, `aero_filewrite.m`, `aero_fileplot.m`
