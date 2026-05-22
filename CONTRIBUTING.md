# Contributing

## Development setup

```bash
git clone https://github.com/brio50/avl-aero-tables.git
cd avl-aero-tables
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
```

## Running tests

```bash
pytest                        # full suite
pytest -k avl_fileread        # single test file
```

```{note}
Integration tests that invoke the AVL binary are skipped automatically if `~/bin/avl` is not present. See {doc}`/user/install` for binary setup.
```

## Serving docs locally

```bash
sphinx-autobuild docs docs/_build/html
# open http://127.0.0.1:8000
```

The server watches for file changes and rebuilds automatically.


## Publishing a release

Pushing a `v*` tag triggers the full `publish.yml` pipeline:

1. **Tests** — full matrix (Python 3.12 + 3.13) must pass
2. **Version check** — tag (e.g. `v1.5.0`) must match `version` in `pyproject.toml`
3. **PyPI publish** — wheel + sdist uploaded via OIDC trusted publishing
4. **GitHub Release** — created automatically with notes pulled from the matching `## [X.Y.Z]` section of `CHANGELOG.md`

Before tagging:

1. Bump `version` in `pyproject.toml`
2. Add a `## [X.Y.Z] - YYYY-MM-DD` section to `CHANGELOG.md`
3. Commit and merge to `main`

Then tag from `main`:

```bash
git tag v1.5.0
git push origin v1.5.0
```

Prerequisites (one-time setup):

- A `pypi` environment must exist in the repository settings (Settings → Environments)
- PyPI must have a trusted publisher configured: repository `brio50/avl-aero-tables`, workflow `publish.yml`, environment `pypi`

## Code style

Linting is handled by [Ruff](https://docs.astral.sh/ruff/):

```bash
ruff check avl_aero_tables tests/
ruff check --fix avl_aero_tables tests/
```
