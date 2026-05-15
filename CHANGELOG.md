
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-09 to 2025-05-15

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
