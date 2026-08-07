"""YAML project-file schema and loader."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError, field_validator

from avl_aero_tables.avl_sweep import _normalize_out_format


class InputSpec(BaseModel):
    geometry: str


class SweepSpec(BaseModel):
    alpha: list[float]
    beta: list[float]
    ctrl_sweeps: dict[str, list[float]] = {}

    @field_validator("alpha", "beta")
    @classmethod
    def non_empty(cls, v: list[float]) -> list[float]:
        if not v:
            raise ValueError("must contain at least one value")
        return v

    @field_validator("ctrl_sweeps")
    @classmethod
    def ctrl_sweeps_non_empty_lists(
        cls, v: dict[str, list[float]]
    ) -> dict[str, list[float]]:
        empty = [k for k, vals in v.items() if not vals]
        if empty:
            raise ValueError(
                f"ctrl_sweeps entries must have at least one value: {empty}"
            )
        missing = [k for k, vals in v.items() if not any(abs(x) < 1e-9 for x in vals)]
        if missing:
            warnings.warn(
                f"ctrl_sweeps surfaces {missing} have no 0.0 deflection — "
                "inserting 0.0 so stability tables are populated.",
                UserWarning,
                stacklevel=2,
            )
            v = {
                k: sorted(vals + [0.0]) if k in missing else vals
                for k, vals in v.items()
            }
        return v


class OutputSpec(BaseModel):
    """``format`` accepts everything ``avl_sweep.run()``'s ``out_format`` does:
    a bare string (``"csv"``, ``"json"``, ``"mat"``, ``"h5"``, or the
    backward-compat ``"df"``) or a list of any combination (e.g.
    ``["csv", "mat"]``).  Stored as-given (not normalized to a list here) so
    existing ``format: csv``-style project files keep round-tripping as a
    plain string; ``avl_sweep.run()`` normalizes it the same way regardless
    of whether it receives a string or a list.  Unlike ``run()``'s own
    default (empty/in-memory-only), this field still defaults to ``"csv"``
    — the CLI must not inherit the bare-API default.
    """

    format: str | list[str] = "csv"

    @field_validator("format")
    @classmethod
    def valid_format(cls, v: str | list[str]) -> str | list[str]:
        _normalize_out_format(v)  # raises ValueError for unrecognised values
        return v


class ProjectConfig(BaseModel):
    input: InputSpec
    sweep: SweepSpec
    output: OutputSpec = OutputSpec()


def load_config(yml_path: Path) -> ProjectConfig:
    try:
        with yml_path.open() as f:
            raw = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        print(f"ERROR: could not parse {yml_path}:\n{exc}", file=sys.stderr)
        sys.exit(1)
    try:
        return ProjectConfig.model_validate(raw)
    except ValidationError as exc:
        print(f"ERROR: invalid project file {yml_path}:\n{exc}", file=sys.stderr)
        sys.exit(1)
