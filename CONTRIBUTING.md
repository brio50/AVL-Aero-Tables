# Contributing

## Development setup

```bash
git clone https://github.com/brio50/avl-wrapper.git
cd avl-wrapper
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
Integration tests that invoke the AVL binary are skipped automatically if `~/bin/avl` is not present. See {doc}`getting-started` for binary setup.
```

## Serving docs locally

```bash
sphinx-autobuild docs docs/_build/html
# open http://127.0.0.1:8000
```

The server watches for file changes and rebuilds automatically.


## Code style

Linting is handled by [Ruff](https://docs.astral.sh/ruff/):

```bash
ruff check avl_wrapper
ruff check --fix avl_wrapper
```
