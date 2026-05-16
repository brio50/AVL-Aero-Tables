
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.4.1] - 2026-05-16

### Added
- `avl_fileplot`: coordinate triads on geometry plot — AVL world frame (X/Y/Z, grey) at the coordinate origin (0, 0, 0); aircraft body frame (x_b/y_b/z_b, RGB) at the CG; legend distinguishes the two frames
- Sphinx docs: plotly figures embedded as lazy-loading iframes with `onload` auto-resize; page weight reduced from ~500 KB to ~47 KB; eliminates CDN version mismatch between Sphinx and generated figures

### Changed
- `avl_fileplot`: four-panel view (Isometric / Top / Front / Side) replaced with a single interactive 3-D scene — user rotates freely
- `avl_fileplot`: equal-axis scaling via `aspectmode="manual"` with explicit per-axis ranges; true geometric proportions preserved
- `avl_fileplot`: matplotlib removed entirely; plotly is the only backend

### Fixed
- `avl_fileplot`: geometry plot now applies each surface's `SCALE` transformation before plotting; previously only `TRANSLATE` was applied, causing surfaces with a Z scale factor (e.g. the b737 wing uses `SCALE 1.0 1.0 0.07`) to plot at grossly incorrect Z values

## [1.4.0] - 2026-05-16

### Added
- `avl_config.py` — new module holding `InputSpec`, `SweepSpec`, `OutputSpec`, `ProjectConfig`, and `load_config()`; extracted from `avl_cli.py` to separate schema/validation concerns from CLI dispatch
- YAML validation now rejects `ctrl_sweeps` entries with empty deflection lists (e.g. `elevator: []`)
- YAML validation now rejects malformed YAML files with a clean error message (previously raised an unhandled `yaml.YAMLError`)
- `avl-aero-tables sweep` validates `ctrl_sweeps` keys against control surface names in the `.avl` file before running; exits with a clear error listing the bad keys and valid surface names
- `examples/b737.py` — Boeing 737-800 end-to-end walkthrough (geometry → sweep → aero database → interactive plots); `--docs` flag writes standalone HTML to `docs/_static/html/`
- `avl_fileplot` and `aero_fileplot` rewritten for plotly; interactive figures embed directly in Sphinx docs and are drop-in compatible with Dash (`dcc.Graph(figure=fig)`) — the `backend` parameter was removed in 1.4.1 when matplotlib support was dropped entirely
- `plotly` added to core package dependencies

### Changed
- `avl_cli.py` reduced to argument parsing and command dispatch; all Pydantic models and `load_config()` moved to `avl_config.py`
- `examples/quickstart.py` renamed to `examples/bd.py` — same Bubble Dancer walkthrough; name now matches the aircraft
- Quickstart docs restructured: intro split into "Input Structure" and "Project Layout" sections; CLI section uses Bubble Dancer (`bd.avl`), Python API section uses Boeing 737-800 (`b737.avl`); B737 plots are now interactive plotly embeds
- `docs/user/reference/api/avl_fileread.md` description updated to cover both parsers (`.avl` geometry and `.st` stability output); stale `st_fileread.md` (orphaned when the module was merged into `avl_fileread`) removed

### Fixed
- `avl_fileplot` matplotlib backend: geometry axes now have equal scale across all three dimensions; previously `set_aspect('equal')` equalized the bounding box but not the data ranges, causing wide-span aircraft (e.g. 737) to appear proportionally wrong

## [1.3.0] - 2026-05-16

### Added
- Structured run output directory with reproducibility artifacts:
  - `.in/` — AVL-generated inputs (`reset.run`, `sweep.inp`)
  - `.in/<avl_stem>/` — snapshot of all user input files at run time (`.avl`, `.yml` for CLI runs, and all referenced airfoil/body `.dat` files discovered from `AFIL`/`BFIL` entries)
  - `.raw/` — raw AVL output files (`case_*.st`)
  - `provenance.json` at run root — records `timestamp`, `package_version`, `git_commit`, `git_branch`, `git_dirty`, `entry` (`"cli"` or `"api"`), `source` (input directory), and `snapshot` (relative path to `.in/<avl_stem>/`)
- `avl_sweep.run()` gains `yml_file` parameter — when provided by the CLI, marks `entry: "cli"` in `provenance.json` and copies the `.yml` into `.in/<avl_stem>/`
- `--version` flag added to the `avl-aero-tables` CLI; reads version from `pyproject.toml` (source of truth) with `importlib.metadata` fallback for non-editable installs

### Changed
- `sweep.log` renamed to `sweep.inp` (`.inp` is the conventional extension for stdin-fed solver scripts in scientific computing) and moved from run root to `.in/`
- `reset.run` moved from run root to `.in/`
- `case_*.st` files moved from run root to `.raw/`
- `results.csv` / `results.json` remain at run root alongside `provenance.json`
- `avl-aero-tables plot aero` updated to read `.st` files from `.raw/` subdirectory
- `provenance.json` `source` field changed from file path (`.avl` or `.yml`) to the input directory — more accurate since `.avl` depends on co-located airfoil/body `.dat` files
- `provenance.json` `package_version` reads from `pyproject.toml` directly rather than `importlib.metadata` — stays current during local development without reinstalling

## [1.2.0] - 2026-05-15

### Changed
- `plot aero` argument changed from `<yml>` to `<runs_dir>` — pass a parent directory to auto-select the latest timestamped run, or a specific timestamped directory for a particular run; `.yml` is no longer required
- `avl_sweep()` `out_dir` is now a **base directory** — the timestamped run directory `{out_dir}/{avl_stem}_{YYYY-MM-DD-HHMMSS}/` is created automatically (including parents); raises `TypeError` if omitted
- All aircraft geometry files consolidated under `examples/` alongside the runnable scripts, mirroring the recommended user project layout: `examples/bd/`, `examples/supra/`, `examples/allegro/`, `examples/b737/`, `examples/plane/`, `examples/supergee/`, `examples/ellipg/`
- `docs/_static/gen_plots.py` merged into `examples/quickstart.py` — single runnable script does geometry read/plot, full alpha × beta × all-controls sweep, aero database, and all coefficient plots; `--docs` flag also writes PNGs to `docs/_static/img/`
- Output directory convention: `runs/bd_<timestamp>/` at project root (gitignored); `examples/quickstart.py` passes `out_dir=Path("runs")` and `avl_sweep` creates the timestamped subdir automatically
- AVL is now invoked as `avl` with **no positional CLI arguments** — geometry and run-case are loaded via `LOAD` and `CASE` stdin commands at the top of the script, making the approach fully consistent with the original MATLAB implementation (`avl < command.txt`); `avl_bin.run()` drops its `avl_file` and `run_file` kwargs accordingly
- `make_run_command()` gains `avl_file` and `run_file` parameters and now emits `LOAD <avl_file>` and `CASE <run_file>` at the top of the generated stdin script
- `sweep.log` now contains the complete stdin script including `LOAD` and `CASE` — a full record of everything piped to AVL; replay claim removed from docs

### Added
- `examples/quickstart.py` — end-to-end walkthrough script (geometry → sweep → aero database → plots); outputs to `runs/bd_<timestamp>/`; `--docs` flag updates committed doc images

### Fixed
- Docstring examples in `avl_sweep`, `aero_filewrite`, and `aero_fileplot` now pass `out_dir` to `avl_sweep()` — previously would raise `TypeError` when run as doctests
- Quickstart docs clarified that `fig.savefig()` writes to the current working directory
- `sweep.log` replay claim removed — the file uses full `run_dir` paths for human readability which exceed AVL's ~80-char Fortran limit; `sweep.log` is a record, not a runnable script

## [1.1.0] - 2026-05-15

### Fixed
- All usage guide and docstring examples corrected from `"examples/bd.avl"` to `"examples/bd/bd.avl"` — paths were stale since the 1.1.0 examples reorganization into per-aircraft subdirectories; copy-paste code would have raised `FileNotFoundError`
- `avl-upstream.md` clarified that `.mass` files are not required by `avl-aero-tables` — `.st` stability derivatives are computed by AVL's vortex lattice solver without mass/inertia data; mass is only needed for dynamic stability eigenvalue (`.eig`) output
- `docs/dev/reqs/sweep.csv` req-sweep-8 had a dead test link (`test_run_default_out_dir_is_relative_to_avl`) and wrong description — corrected to match the actual test name and behavior (CWD-relative timestamped directory, not avl_dir-relative)

### Added
- YAML-driven CLI: `avl-aero-tables sweep <yml>`, `plot geometry <yml>`, `plot aero <runs_dir>` — replaces the removed `run <command_file>` subcommand
- `examples/<stem>/<stem>.yml` project files for all seven reference aircraft (bd, allegro, b737, ellipg, plane, supergee, supra)
- `ProjectConfig` / `InputSpec` / `SweepSpec` / `OutputSpec` pydantic models — parse and validate the project file; report structured errors on bad input
- `sweep.log` written to each output directory — records the stdin commands piped to AVL with a replay comment on the first line showing the exact shell invocation
- `reset.run` is now a real AVL CLI input (written to a short `/tmp` staging path and passed as the second positional argument to the binary) rather than a reference-only file

### Changed
- YAML project file schema: `input.geometry` (path to `.avl`, relative to yml), `sweep.{alpha,beta,ctrl_sweeps}`, `output.format` (default `csv`)
- Sweep output directory: `<yml_dir>/../runs/<stem>/<YYYY-MM-DD-HHMMSS>/` — e.g. `examples/bd/bd.yml` → `examples/runs/bd/2026-05-15-120000/`
- `plot aero` takes a `<runs_dir>` path — pass a parent directory to auto-select the latest timestamped run, or a specific directory for a particular run
- `run <command_file>` subcommand removed — was never the intended interface
- AVL is now invoked using its documented CLI interface: `avl <avl_file> <reset.run>`, matching the original MATLAB implementation; geometry loading via the `LOAD` stdin command has been removed
- `make_run_command()` no longer accepts `avl_name` parameter — this is now a CLI argument handled by `avl_bin.run()`; the generated stdin script begins with `PLOP G` then `OPER` rather than `LOAD`
- `avl_bin.run()` gains `avl_file` and `run_file` keyword arguments passed as positional CLI args to the AVL binary
- `sweep.cmd` renamed to `sweep.log` to accurately reflect that it is a record of what was sent, not a driver file
- Custom geometry documentation added to usage guide: recommended project layout for `.avl` and associated airfoil data files
- `examples/` reorganized: ~80 redundant and standalone AVL models removed, leaving six curated aircraft (Bubble Dancer, Allegro-Lite, Boeing 737-800, Plane Vanilla, SuperGee, Supra); each lives in its own subfolder with all referenced airfoil `.dat` and body `.dat` files co-located; `ellipg.avl` (wing-only test fixture) moved to `tests/data/`

### Removed
- `mass_file` parameter removed from `avl_sweep()` and `avl_bin.run()` — `.st` stability and control derivatives do not depend on mass or inertia properties; `.mass` files are only needed for AVL's dynamic stability eigenvalue analysis (`.eig`), which is outside the scope of this package

### Dependencies
- Added `pyyaml` and `pydantic` to `[project] dependencies`

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
