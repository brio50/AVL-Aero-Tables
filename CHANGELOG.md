
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-05-09

### Added
- Sphinx docs site deployed to GitHub Pages: getting-started, usage, API reference, roadmap, contributing, changelog, and embedded AVL upstream reference
- GitHub Actions workflow for automatic docs deployment on push to master
- `CONTRIBUTING.md` with dev setup, test, and docs-serve instructions
- Bubble Dancer example plots embedded in getting-started
- Full Python port of all eight MATLAB modules into the `avl_aero_tables` package
- `avl()` as the primary entry point; `out_format` parameter writes results to `"csv"` (default), `"json"`, or `"df"` (DataFrame in memory only)
- `results_to_dataframe()` converts `list[StResult]` to a pandas DataFrame for tabular export
- `avl-aero-tables` CLI with `verify` and `run` subcommands
- GitHub Actions CI workflow; builds AVL 3.52 from source on Ubuntu on every push
- 158-test pytest suite covering all modules (unit + integration)

### Changed
- Minimum Python version raised to 3.12; CI matrix updated to 3.12 and 3.13
- README trimmed to a short landing page pointing at the docs site
- GitHub repository renamed from `Matlab-AVL-Wrapper` to `avl-aero-tables`
- `aero_filewrite` stability tables populated only for neutral-control runs; fixes a known bug carried over from the MATLAB implementation
- `aero_fileplot` beta-index lookup is now generic rather than hardcoded to a specific surface name
- Type annotations and error messages improved across all public functions

### Removed
- MATLAB source files (`.m`) removed from working tree; originals preserved at git tag `v0.0.0-matlab`
- `examples/avl.exe` Windows binary and `tmp/` directory (MATLAB holdovers)

## [0.0.0] - 2014-08-28

### Notes
- Initial MATLAB-based implementation; see tag `v0.0.0-matlab`
- Modules: `avl.m`, `avl_fileread.m`, `avl_fileplot.m`, `avl_rungen.m`,
  `st_fileread.m`, `avl_aerogen.m`, `aero_filewrite.m`, `aero_fileplot.m`
