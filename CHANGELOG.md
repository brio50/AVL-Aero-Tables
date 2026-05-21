# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.7.0] - 2026-05-20

### Added
- Structured logging via Python `logging` module throughout `avl_aero_tables`
- Per-run log file written to `{run_dir}/{avl_name}.log` on every sweep (always, regardless of `--quiet`); captures WARNING and above from the whole package
- Rich indeterminate spinner during the blocking AVL subprocess call; shown only in a TTY, suppressed when piped or `--quiet`
- `rich` added to core dependencies

### Changed
- `verbose` module flag removed; console output is now controlled by the standard Python logging system — API users call `logging.basicConfig(level=logging.INFO)` to enable it, or `logging.getLogger("avl_aero_tables").setLevel(logging.WARNING)` to suppress
- CLI `--quiet` / `-q` suppresses the console logging handler (log file is still written)
- `_ensure_neutral_in_sweeps` 0.0 auto-insertion now emits `_log.warning()` instead of `warnings.warn(UserWarning)`, so it appears in the run log file
- `aero_filewrite` verbose summary print removed (was redundant with user-supplied sweep parameters)
- Quickstart docs: all CLI and Python API examples use unified Input/Output card layout

## [1.6.0] - 2026-05-16

### Changed
- Plotly modebar always visible; styled with vertical orientation and translucent background
- Geometry figure whitespace tightened; view buttons (Iso / Right / Front / Top) with corrected camera positions; Iso camera reoriented so nose points toward the viewer (lower-right)
- Aero coefficient figure margins and title centering improved; `CAMERA_AERO` constant added to `_plot_config`
- Quickstart docs: MyST comments added pointing to plot regeneration scripts

## [1.5.0] - 2026-05-16

### Added
- `_plot_config.py` — shared Plotly constants (`AXIS_3D`, camera defaults, colorscales, opacity); all plot modules import from here
- `equal_3d_ranges()` helper extracted to `_plot_config` for reuse
- `ctrl_sweeps` entries missing `0.0` now trigger a `UserWarning` and auto-insert it, ensuring stability tables are always populated
- Coordinate triads on geometry plot (AVL world frame + aircraft body frame at CG); legend distinguishes the two frames
- Sphinx plotly figures embedded as lazy-loading iframes; `:height:` and `:class:` options on the `plotly-figure` directive

### Changed
- `avl_fileplot`: single interactive 3-D scene replaces four-panel static view; equal-axis scaling; background planes removed
- `aero_fileplot`: consistent margins and subplot title sizing

### Fixed
- CLI sweep output directory regression (`runs/` → `_runs/`)
- Geometry `SCALE` transformation now applied before plotting (previously only `TRANSLATE` was applied)

## [1.4.0] - 2026-05-16

### Added
- `avl_config.py` — Pydantic models (`ProjectConfig`, `InputSpec`, `SweepSpec`, `OutputSpec`) and `load_config()`; YAML validation with clear error messages
- YAML-driven CLI: `sweep <yml>`, `plot geometry <yml>`, `plot aero <runs_dir>`
- `avl_fileplot` and `aero_fileplot` rewritten for Plotly; interactive figures embed in Sphinx and Dash
- `examples/b737.py` — Boeing 737-800 end-to-end walkthrough with `--docs` flag
- `plotly` added to core dependencies

### Changed
- Quickstart restructured: CLI section uses Bubble Dancer, Python API section uses B737
- `examples/quickstart.py` renamed to `examples/bd.py`

## [1.3.0] - 2026-05-16

### Added
- Structured run output: `.in/` (inputs + geometry snapshot), `.raw/` (`.st` files), `provenance.json` (timestamp, version, git state, entry point)
- `--version` CLI flag

### Changed
- `sweep.log` → `sweep.inp`, moved to `.in/`; `reset.run` and `case_*.st` reorganized into `.in/` and `.raw/`

## [1.2.0] - 2026-05-15

### Added
- `examples/bd.py` end-to-end walkthrough with `--docs` flag

### Changed
- `plot aero` accepts a parent `<runs_dir>` (latest run auto-selected) instead of a `.yml`
- `avl_sweep()` `out_dir` is a base directory; timestamped subdirectory created automatically
- AVL invoked as pure stdin script (`avl < script`); `LOAD` / `CASE` commands at top of script
- `examples/` reorganized into per-aircraft subdirectories with co-located airfoil data

## [1.1.0] - 2026-05-15

### Added
- YAML project file schema (`input`, `sweep`, `output` sections); Pydantic validation
- `sweep <yml>`, `plot geometry <yml>`, `plot aero <runs_dir>` CLI subcommands
- Project files for all seven reference aircraft

### Removed
- `mass_file` parameter (not needed for `.st` vortex-lattice output)
- `run <command_file>` CLI subcommand

## [1.0.1] - 2026-05-15

### Fixed
- Add missing `docs/dev/reqs/sweep.csv` (was excluded by an overly broad `.gitignore` pattern), docs action fix!
- Remove unused `sphinx.ext.intersphinx` extension and its four network fetches at build time

## [1.0.0] - 2026-05-09 to 2026-05-15

### Added
- `docs/dev/requirements.md` — per-module behavioral requirements derived from the test suite, rendered as eight `csv-table` sections (one per module)
- `docs/dev/reqs/` — eight source CSVs (`geom`, `stab`, `cmd`, `bin`, `sweep`, `plot`, `write`, `aeroplot`), each with `id`, `requirement`, `rationale`, and `test` columns; test column links to the covering function on GitHub
- `@pytest.mark.req("req-xxx")` decorators on all 84 requirement-linked tests; `tests/conftest.py` prints a requirement-coverage summary at the end of every run
- Sphinx docs site deployed to GitHub Pages: getting-started, usage, API reference, roadmap, contributing, changelog, and embedded AVL upstream reference
- GitHub Actions workflow for automatic docs deployment on push to master; PyPI publish workflow
- `CONTRIBUTING.md` with dev setup, test, and docs-serve instructions
- Bubble Dancer example plots embedded in getting-started
- Full Python port of all eight MATLAB modules into the `avl_aero_tables` package
- `avl_sweep()` as the primary entry point; `out_format` parameter writes results to `"csv"` (default), `"json"`, or `"df"` (DataFrame in memory only)
- `results_to_dataframe()` converts `list[StResult]` to a pandas DataFrame for tabular export
- `avl-aero-tables` CLI with `verify` and `run` subcommands
- GitHub Actions CI workflow; builds AVL 3.52 from source on Ubuntu on every push
- 172-test pytest suite with `--doctest-modules`; all public functions have runnable docstring examples
- mypy static type checking across all modules
- File-based AVL inputs: `reset.run` (AVL run-case format, all conditions zeroed) and `sweep.cmd` (full stdin command script) are written to the output directory before each run, so inputs and outputs are always on disk together; a run can be replayed manually with `avl < sweep.cmd`
- Timestamped output subdirectories (`out/<name>/YYYY-MM-DD-HHMMSS/`) created by default so previous results are never overwritten; pass an explicit `out_dir` to write to a fixed location instead
- `avl_sweep()` prints the output path and case count on completion: `AVL sweep complete → out/bd/2026-05-15-143022  (12 cases)`

### Changed
- Minimum Python version raised to 3.12; CI matrix updated to 3.12 and 3.13
- README trimmed to a short landing page pointing at the docs site
- GitHub repository and Python package renamed to `avl-aero-tables` / `avl_aero_tables`
- `avl_aerogen` renamed to `avl_sweep`; CLI split from `avl_bin` into `avl_cli`
- Docs restructured into `docs/user/` and `docs/dev/` sections
- `aero_filewrite` stability tables populated only for neutral-control runs; fixes a known bug carried over from the MATLAB implementation
- `aero_fileplot` beta-index lookup is now generic rather than hardcoded to a specific surface name
- Type annotations and error messages improved across all public functions
- `make_reset_run` / `make_command` renamed to `make_run_reset` / `make_run_command` for a consistent `make_run_` prefix
- Default `out_dir` changed from `<avl_file_parent>/out/<name>/` to `out/<name>/` relative to the current working directory
- When an explicit `out_dir` is provided, only stale `.st` files are removed before the run; other files (e.g. a previous `results.csv`) are left untouched

### Removed
- MATLAB source files (`.m`) removed from working tree; originals preserved at git tag `v0.0.0-matlab`
- `examples/avl.exe` Windows binary and `tmp/` directory (MATLAB holdovers)

## [0.0.0] - 2014-08-28

### Notes
- Initial MATLAB-based implementation; see tag `v0.0.0-matlab`
- Modules: `avl.m`, `avl_fileread.m`, `avl_fileplot.m`, `avl_rungen.m`,
  `st_fileread.m`, `avl_aerogen.m`, `aero_filewrite.m`, `aero_fileplot.m`
