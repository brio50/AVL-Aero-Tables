"""Parse AVL stability derivative output files (.st)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class StResult:
    filename: str
    controls: dict[str, str] = field(default_factory=dict)  # "d01" -> "flap"
    data: dict[str, float] = field(default_factory=dict)  # "CLa" -> 5.631


def _sanitize(name: str) -> str:
    return name.replace("/", "_div_").replace("'", "_prime_")


def _parse_st_file(path: Path) -> StResult:
    result = StResult(filename=path.name)
    lines = path.read_text().splitlines()
    tokens = " ".join(lines[1:]).split()  # skip line 0 (the dashed separator)

    ctrl_re = re.compile(r"^d\d")

    for idx, tok in enumerate(tokens):
        if ctrl_re.match(tok) and idx > 0:
            result.controls[tok] = tokens[idx - 1]

        if tok == "=" and idx > 0 and idx + 1 < len(tokens):
            # "Clb Cnr / Clr Cnb = <value>" — 5-token compound name
            if (
                idx >= 5
                and tokens[idx - 5] == "Clb"
                and tokens[idx - 4] == "Cnr"
                and tokens[idx - 3] == "/"
                and tokens[idx - 2] == "Clr"
            ):
                var = "Clb_Cnr_div_Clr_Cnb"
            else:
                var = _sanitize(tokens[idx - 1])
            try:
                result.data[var] = float(tokens[idx + 1])
            except ValueError:
                pass

    return result


def st_fileread(path: str | Path) -> list[StResult]:
    """Parse .st files and return a list of StResult (one per file).

    Accepts either a directory (reads all ``*.st`` files) or a single ``.st`` file.

    Example
    -------
    >>> from avl_wrapper.st_fileread import st_fileread
    >>> results = st_fileread("tests/data/bd_alpha5_beta0.st")
    >>> len(results)
    1
    >>> results[0].filename
    'bd_alpha5_beta0.st'
    >>> results[0].data["Alpha"]
    5.0
    >>> results[0].data["CLtot"]
    0.58447
    >>> results[0].controls
    {'d01': 'flap', 'd02': 'aileron', 'd03': 'elevator', 'd04': 'rudder'}
    """
    path = Path(path)
    if path.is_dir():
        files = sorted(path.glob("*.st"))
    else:
        files = [path]

    return [_parse_st_file(f) for f in files]
