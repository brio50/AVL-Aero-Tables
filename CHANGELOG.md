# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Python package `avl_wrapper` with modules ported from MATLAB sources
- `pyproject.toml` using setuptools; installable via `pip install python-avl-wrapper`
- AVL 3.52 example geometry and run files in `examples/`
- `CHANGELOG.md`, `README.md` updated for Python project

### Removed
- MATLAB source files (`.m`) archived to git history; tagged `v0.0.0-matlab` on `master`
- `examples/avl.exe` Windows PE32 binary (not applicable on macOS/Linux)
- `tmp/` directory (MATLAB command file holdover; now generated in-memory via `tempfile`)

## [0.0.0] - 2014-08-28

### Notes
- Initial MATLAB-based implementation; see tag `v0.0.0-matlab`
- Modules: `avl.m`, `avl_fileread.m`, `avl_fileplot.m`, `avl_rungen.m`,
  `st_fileread.m`, `avl_aerogen.m`, `aero_filewrite.m`, `aero_fileplot.m`
