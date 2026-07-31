"""Parse AVL file formats: geometry inputs (.avl) and stability outputs (.st)."""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AvlHeader:
    name: str = ""
    Mach: float = 0.0
    iYsym: int = 0
    iZsym: int = 0
    Zsym: float = 0.0
    Sref: float = 0.0
    Cref: float = 0.0
    Bref: float = 0.0
    Xref: float = 0.0
    Yref: float = 0.0
    Zref: float = 0.0
    CDoref: float = 0.0


@dataclass
class AvlControlEntry:
    """One control-surface definition attached to a section."""

    name: str
    gain: float
    xhinge: float
    xyzhvec: tuple[float, float, float]
    sgn_dup: float = 1.0


@dataclass
class AvlDesignEntry:
    """One design-variable perturbation attached to a section."""

    name: str
    weight: float


@dataclass
class AvlSectionEntry:
    """One chordwise section of a lifting surface."""

    xle: float
    yle: float
    zle: float
    chord: float
    ainc: float = 0.0
    nspan: float = 0.0
    sspan: float = 0.0
    naca: str | None = None
    afile: str | None = None
    claf: float | None = None
    controls: list[AvlControlEntry] = field(default_factory=list)
    airfoil_coords: list[tuple[float, float]] = field(default_factory=list)
    airfoil_x1: float = 0.0
    airfoil_x2: float = 1.0
    design: list[AvlDesignEntry] = field(default_factory=list)


@dataclass
class AvlSurface:
    nchord: float = 0.0
    cspace: float = 0.0
    nspan: float | str = ""
    sspace: float | str = ""
    ydupl: float | str = ""
    lcomp: float | None = None
    scale: list[float] | None = None
    trans: list[float] | None = None
    dainc: float | None = None
    nowake: bool = False
    noalbe: bool = False
    noload: bool = False
    sections: list[AvlSectionEntry] = field(default_factory=list)


@dataclass
class AvlBody:
    name: str = ""
    nbody: float = 0.0
    bspace: float = 0.0
    ydupl: float | str = ""
    scale: list[float] | None = None
    trans: list[float] | None = None
    bfile: str = ""
    bfile_x: list[float] = field(default_factory=list)
    bfile_y: list[float] = field(default_factory=list)


@dataclass
class AvlGeometry:
    header: AvlHeader = field(default_factory=AvlHeader)
    body: AvlBody | None = None
    surface: dict[str, AvlSurface] = field(default_factory=dict)

    @property
    def ctrl_names(self) -> list[str]:
        """Return ordered unique control-surface names across all surfaces.

        Example
        -------
        >>> from avl_aero_tables.avl_fileread import avl_fileread
        >>> geom = avl_fileread("examples/bd/bd.avl")
        >>> geom.ctrl_names
        ['flap', 'aileron', 'elevator', 'rudder']
        """
        all_names = (
            ctrl.name
            for surf in self.surface.values()
            for section in surf.sections
            for ctrl in section.controls
            if ctrl.name
        )
        return list(dict.fromkeys(all_names))


def _to_valid_key(name: str) -> str:
    """Convert a surface name to a valid Python identifier (mirrors MATLAB genvarname)."""  # noqa: E501
    key = name.strip().replace(" ", "_").replace("-", "_")
    if key and key[0].isdigit():
        key = "x" + key
    return key


def _floats(line: str) -> list[float]:
    """Parse leading numeric tokens from a line, stopping at non-numeric text."""
    result = []
    for token in line.split():
        try:
            result.append(float(token))
        except ValueError:
            break
    return result


def avl_fileread(avl_file: str | Path) -> AvlGeometry:
    """Parse an AVL geometry file and return an AvlGeometry dataclass tree.

    Example
    -------
    >>> from avl_aero_tables.avl_fileread import avl_fileread
    >>> geom = avl_fileread("examples/bd/bd.avl")
    >>> geom.header.name
    'Bubble Dancer RES'
    >>> list(geom.surface.keys())
    ['Wing', 'Horizontal_tail', 'Vertical_tail']
    >>> geom.ctrl_names
    ['flap', 'aileron', 'elevator', 'rudder']
    """
    avl_file = Path(avl_file)

    eval_lines = [
        line
        for line in avl_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith(("!", "#"))
    ]

    geom = AvlGeometry()
    hdr = geom.header

    hdr.name = eval_lines[0].strip()
    hdr.Mach = _floats(eval_lines[1])[0]
    vals = _floats(eval_lines[2])
    hdr.iYsym, hdr.iZsym, hdr.Zsym = int(vals[0]), int(vals[1]), vals[2]
    vals = _floats(eval_lines[3])
    hdr.Sref, hdr.Cref, hdr.Bref = vals[0], vals[1], vals[2]
    vals = _floats(eval_lines[4])
    hdr.Xref, hdr.Yref, hdr.Zref = vals[0], vals[1], vals[2]

    cdo_vals = _floats(eval_lines[5])
    if cdo_vals:
        hdr.CDoref = cdo_vals[0]
        i = 6
    else:
        i = 5

    n = len(eval_lines)
    cur_surf: AvlSurface | None = None

    while i < n:
        tline = eval_lines[i].strip()

        # BODY and SURFACE are sequential ifs (not elif): after BODY's inner loop
        # exits on a SURFACE line, the SURFACE block fires in the same iteration.

        if tline.upper() == "BODY":
            body = AvlBody()
            geom.body = body
            i += 1
            vals = _floats(eval_lines[i])
            if len(vals) >= 2:
                body.nbody, body.bspace = vals[0], vals[1]
            i += 1

            while i < n and eval_lines[i].strip().upper() != "SURFACE":
                kw = eval_lines[i].strip().upper()
                if kw == "YDUPLICATE":
                    i += 1
                    body.ydupl = _floats(eval_lines[i])[0]
                elif kw == "SCALE":
                    i += 1
                    body.scale = _floats(eval_lines[i])
                elif kw == "TRANSLATE":
                    i += 1
                    body.trans = _floats(eval_lines[i])
                elif kw == "BFIL":
                    i += 1
                    body.bfile = eval_lines[i].strip()
                    bfil_path = avl_file.parent / body.bfile
                    if bfil_path.exists():
                        for bl in bfil_path.read_text().splitlines()[1:]:
                            bparts = bl.split()
                            if len(bparts) >= 2:
                                body.bfile_x.append(float(bparts[0]))
                                body.bfile_y.append(float(bparts[1]))
                    else:
                        warnings.warn(f"Body file not found: {bfil_path}")
                i += 1

            if i >= n:
                break
            tline = eval_lines[i].strip()

        if tline.upper() == "SURFACE":
            i += 1
            surf_name = _to_valid_key(eval_lines[i])
            i += 1
            vals = _floats(eval_lines[i])
            cur_surf = AvlSurface(
                nchord=vals[0],
                cspace=vals[1],
                nspan=vals[2] if len(vals) > 2 else "",
                sspace=vals[3] if len(vals) > 3 else "",
            )
            geom.surface[surf_name] = cur_surf

        elif cur_surf is not None:
            kw = tline.upper()
            if kw == "COMPONENT":
                i += 1
                cur_surf.lcomp = _floats(eval_lines[i])[0]

            elif kw == "YDUPLICATE":
                i += 1
                cur_surf.ydupl = _floats(eval_lines[i])[0]

            elif kw == "SCALE":
                i += 1
                cur_surf.scale = _floats(eval_lines[i])

            elif kw == "TRANSLATE":
                i += 1
                cur_surf.trans = _floats(eval_lines[i])

            elif kw == "ANGLE":
                i += 1
                cur_surf.dainc = _floats(eval_lines[i])[0]

            elif kw == "NOWAKE":
                cur_surf.nowake = True

            elif kw == "NOALBE":
                cur_surf.noalbe = True

            elif kw == "NOLOAD":
                cur_surf.noload = True

            elif kw == "SECTION":
                i += 1
                vals = _floats(eval_lines[i])
                cur_surf.sections.append(
                    AvlSectionEntry(
                        xle=vals[0] if vals else 0.0,
                        yle=vals[1] if len(vals) > 1 else 0.0,
                        zle=vals[2] if len(vals) > 2 else 0.0,
                        chord=vals[3] if len(vals) > 3 else 0.0,
                        ainc=vals[4] if len(vals) > 4 else 0.0,
                        nspan=vals[5] if len(vals) > 5 else 0.0,
                        sspan=vals[6] if len(vals) > 6 else 0.0,
                    )
                )

            elif kw.split()[0] == "NACA":
                i += 1
                cur_surf.sections[-1].naca = eval_lines[i].strip()

            elif kw.split()[0] == "AIRFOIL":
                parts = tline.split()
                sec = cur_surf.sections[-1]
                sec.airfoil_x1 = float(parts[1]) if len(parts) > 1 else 0.0
                sec.airfoil_x2 = float(parts[2]) if len(parts) > 2 else 1.0
                while i + 1 < n and len(_floats(eval_lines[i + 1])) >= 2:
                    i += 1
                    vals = _floats(eval_lines[i])
                    sec.airfoil_coords.append((vals[0], vals[1]))

            elif kw == "DESIGN":
                i += 1
                parts = eval_lines[i].split()
                cur_surf.sections[-1].design.append(
                    AvlDesignEntry(name=parts[0], weight=float(parts[1]))
                )

            elif kw.split()[0] == "AFIL":
                i += 1
                cur_surf.sections[-1].afile = eval_lines[i].strip()

            elif kw == "CONTROL":
                i += 1
                parts = eval_lines[i].split()
                if len(parts) < 6:
                    raise ValueError(
                        f"CONTROL line has {len(parts)} tokens, expected at least 6 "
                        f"(name gain xhinge XYZhvec[0-2] [SgnDup]): {eval_lines[i]!r}"
                    )
                cur_surf.sections[-1].controls.append(
                    AvlControlEntry(
                        name=parts[0],
                        gain=float(parts[1]),
                        xhinge=float(parts[2]),
                        xyzhvec=(float(parts[3]), float(parts[4]), float(parts[5])),
                        sgn_dup=float(parts[6]) if len(parts) > 6 else 1.0,
                    )
                )

            elif kw == "CLAF":
                i += 1
                cur_surf.sections[-1].claf = _floats(eval_lines[i])[0]

        i += 1

    return geom


# ---------------------------------------------------------------------------
# .st stability-output parsing
# ---------------------------------------------------------------------------


@dataclass
class StResult:
    filename: str
    controls: dict[str, str] = field(default_factory=dict)  # "d01" -> "flap"
    data: dict[str, float] = field(default_factory=dict)  # "CLa" -> 5.631


def _sanitize_coef_name(name: str) -> str:
    """Remove characters from AVL names that are invalid in Python identifiers."""
    return name.replace("/", "_div_").replace("'", "_prime_")


def _parse_st_file(path: Path) -> StResult:
    result = StResult(filename=path.name)
    lines = path.read_text().splitlines()
    tokens = " ".join(lines[1:]).split()  # skip line 0 (the dashed separator)

    ctrl_token_re = re.compile(r"^d\d+$")  # matches d01, d02, … (one-or-more digits)

    for idx, tok in enumerate(tokens):
        if ctrl_token_re.match(tok) and idx > 0:
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
                var = _sanitize_coef_name(tokens[idx - 1])
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
    >>> from avl_aero_tables.avl_fileread import st_fileread
    >>> results = st_fileread("examples/bd/bd_alpha5_beta0.st")
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
