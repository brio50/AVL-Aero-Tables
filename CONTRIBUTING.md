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


## Publishing to PyPI

Releases are published automatically via GitHub Actions when a version tag is pushed. Tags can be pushed from any branch — to ensure releases only originate from `main`, create the tag from there.

```bash
git tag v1.0.0
git push origin v1.0.0
```

The `publish.yml` workflow builds the distribution and uploads it to PyPI using OIDC trusted publishing — no API token needed. Prerequisites:

- A `pypi` environment must exist in the repository settings (Settings → Environments)
- PyPI must have a trusted publisher configured: repository `brio50/avl-aero-tables`, workflow `publish.yml`, environment `pypi`

## Code style

Linting is handled by [Ruff](https://docs.astral.sh/ruff/):

```bash
ruff check avl_aero_tables
ruff check --fix avl_aero_tables
```
