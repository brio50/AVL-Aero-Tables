
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-09

### Added
- Full Python port of all eight MATLAB modules: `avl_fileread`, `st_fileread`, `avl_rungen`, `avl_bin`, `avl_aerogen`, `avl_fileplot`, `aero_filewrite`, `aero_fileplot`
- `avl()` as the primary public entry point (mirrors MATLAB `avl()` workflow); accepts `out_format` parameter (`"csv"` default, `"json"`, `"df"`) to write results alongside `.st` files
- `results_to_dataframe(results)` in `aero_filewrite`: converts `list[StResult]` to a pandas `DataFrame` for CSV / JSON export
- `avl_fileread` / `avl_fileplot`: parse `.avl` geometry files into `AvlGeometry` dataclass; four-view matplotlib plot
- `st_fileread`: parse AVL `.st` stability output files into `list[StResult]`; fixes `Clb Cnr / Clr Cnb` compound-key bug from MATLAB
- `aero_filewrite`: pivot `list[StResult]` into `AeroDatabase` numpy lookup tables (alpha × beta for stability; alpha × beta × deflection for control)
- `aero_fileplot`: 3-D surface plots of stability and control coefficient tables
- `avl-wrapper` CLI with `verify` and `run` subcommands
- Public API exports: `AvlGeometry`, `StResult`, `StabTable`, `CtrlTable` for user type annotations
- pytest suite: 158 tests covering all modules (unit + integration); `out_format` tested for all supported formats
- GitHub Actions CI workflow (`.github/workflows/test.yml`); builds AVL 3.52 from source on Ubuntu so integration tests run on every push
- End-to-end `README.md` walkthrough using `bd.avl` (Bubble Dancer sailplane)

### Changed
- `avl_wrapper/avl.py` renamed to `avl_wrapper/avl_bin.py` so the `avl` name in the public namespace unambiguously refers to the sweep entry point
- `aero_filewrite` stability tables now populated only for neutral-control runs (all deflections = 0); fixes known MATLAB bug (was a TODO comment in `aero_filewrite.m`)
- `aero_fileplot` beta-index lookup generalised from hardcoded `CLtot_d1_flap` to `np.argmin` over any available beta breakpoints
- `tests/fixtures/` renamed to `tests/data/`; `.st` test data file now tracked in git (was accidentally excluded by `*.st` gitignore rule)
- Python best-practices pass: type annotations on all public functions, `AvlSection.NACA` corrected to `list[str | None]`, CONTROL `SgnDup` default of `1.0` when omitted, `import warnings` moved to module level, informative `ValueError` when `Alpha`/`Beta` missing from `StResult`
- `pandas` added as core dependency for DataFrame output; `scipy` deferred to future work

### Removed
- MATLAB source files (`.m`) removed from working tree; original sources preserved at git tag `v0.0.0-matlab`
- `avl_gui.m` not ported (MATLAB GUI Layout Toolbox; no Python equivalent needed)
- `examples/avl.exe` Windows PE32 binary (not applicable on macOS/Linux)
- `tmp/` directory (MATLAB command file holdover; now generated in-memory via `tempfile`)
- `pandas` and `scipy` were initially listed as unused dependencies and removed, then `pandas` restored for DataFrame output

## [0.0.0] - 2014-08-28

### Notes
- Initial MATLAB-based implementation; see tag `v0.0.0-matlab`
- Modules: `avl.m`, `avl_fileread.m`, `avl_fileplot.m`, `avl_rungen.m`,
  `st_fileread.m`, `avl_aerogen.m`, `aero_filewrite.m`, `aero_fileplot.m`
