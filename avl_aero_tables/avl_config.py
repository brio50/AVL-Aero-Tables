"""YAML project-file schema and loader."""

from __future__ import annotations

import sys
import warnings
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ValidationError, field_validator


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
        missing = [
            k for k, vals in v.items() if not any(abs(x) < 1e-9 for x in vals)
        ]
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
    format: Literal["csv", "json", "df"] = "csv"


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
