"""Parse an AVL geometry file (.avl) into a nested Python structure."""

from __future__ import annotations

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
class AvlSection:
    Xle: list[float] = field(default_factory=list)
    Yle: list[float] = field(default_factory=list)
    Zle: list[float] = field(default_factory=list)
    Chord: list[float] = field(default_factory=list)
    Ainc: list[float] = field(default_factory=list)
    Nspan: list[float] = field(default_factory=list)
    Sspan: list[float] = field(default_factory=list)
    NACA: list[str | None] = field(default_factory=list)
    Afile: list[str | None] = field(default_factory=list)
    CLaf: list[float | None] = field(default_factory=list)


@dataclass
class AvlControl:
    Name: list[list[str]] = field(default_factory=list)
    Gain: list[list[float]] = field(default_factory=list)
    Xhinge: list[list[float]] = field(default_factory=list)
    XYZhvec: list[list[float]] = field(default_factory=list)
    SgnDup: list[list[float]] = field(default_factory=list)


@dataclass
class AvlSurface:
    Nchord: float = 0.0
    Cspace: float = 0.0
    Nspan: float | str = ""
    Sspace: float | str = ""
    Ydupl: float | str = ""
    Lcomp: float | None = None
    Scale: list[float] | None = None
    Trans: list[float] | None = None
    dAinc: float | None = None
    NOWAKE: bool = False
    NOALBE: bool = False
    NOLOAD: bool = False
    SECTION: AvlSection = field(default_factory=AvlSection)
    CONTROL: AvlControl = field(default_factory=AvlControl)


@dataclass
class AvlBody:
    Name: str = ""
    Nbody: float = 0.0
    Bspace: float = 0.0
    Ydupl: float | str = ""
    Scale: list[float] | None = None
    Trans: list[float] | None = None
    Bfile: str = ""
    Bfile_X: list[float] = field(default_factory=list)
    Bfile_Y: list[float] = field(default_factory=list)


@dataclass
class AvlGeometry:
    header: AvlHeader = field(default_factory=AvlHeader)
    body: AvlBody | None = None
    surface: dict[str, AvlSurface] = field(default_factory=dict)


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
    """Parse an AVL geometry file and return an AvlGeometry dataclass tree."""
    avl_file = Path(avl_file)

    raw_lines = avl_file.read_text().splitlines()

    eval_lines: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("!") and not stripped.startswith("#"):
            eval_lines.append(line)

    geom = AvlGeometry()
    hdr = geom.header

    hdr.name = eval_lines[0].strip()

    vals = _floats(eval_lines[1])
    hdr.Mach = vals[0]

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
        i = 5  # no CDoref line; eval_lines[5] is the first keyword
    n = len(eval_lines)
    surf_name: str = ""
    sect_num: int = 0
    ctrl_num: int = 0

    while i < n:
        tline = eval_lines[i].strip()

        # BODY and SURFACE are separate if-blocks (not elif) matching MATLAB:
        # after BODY's inner loop exits at "SURFACE", the SURFACE block fires
        # in the same outer iteration.

        if tline.upper() == "BODY":
            body = AvlBody(Name=tline)
            geom.body = body
            i += 1
            # MATLAB advances once and reads as floats; "Name" line yields []
            vals = _floats(eval_lines[i])
            if len(vals) >= 2:
                body.Nbody, body.Bspace = vals[0], vals[1]
            i += 1

            while i < n and eval_lines[i].strip().upper() != "SURFACE":
                kw = eval_lines[i].strip().upper()
                if kw == "YDUPLICATE":
                    i += 1
                    body.Ydupl = _floats(eval_lines[i])[0]
                elif kw == "SCALE":
                    i += 1
                    body.Scale = _floats(eval_lines[i])
                elif kw == "TRANSLATE":
                    i += 1
                    body.Trans = _floats(eval_lines[i])
                elif kw == "BFIL":
                    i += 1
                    body.Bfile = eval_lines[i].strip()
                    bfil_path = avl_file.parent / body.Bfile
                    if bfil_path.exists():
                        blines = bfil_path.read_text().splitlines()[1:]
                        for bl in blines:
                            bparts = bl.split()
                            if len(bparts) >= 2:
                                body.Bfile_X.append(float(bparts[0]))
                                body.Bfile_Y.append(float(bparts[1]))
                    else:
                        warnings.warn(f"Body file not found: {bfil_path}")
                i += 1
            # i now points at "SURFACE" (or end of file) — refresh for fall-through
            if i >= n:
                break
            tline = eval_lines[i].strip()

        if tline.upper() == "SURFACE":
            sect_num = 0
            i += 1
            surf_name = _to_valid_key(eval_lines[i])
            i += 1
            vals = _floats(eval_lines[i])
            surf = AvlSurface(
                Nchord=vals[0],
                Cspace=vals[1],
                Nspan=vals[2] if len(vals) > 2 else "",
                Sspace=vals[3] if len(vals) > 3 else "",
            )
            geom.surface[surf_name] = surf

        elif tline.upper() == "COMPONENT":
            i += 1
            geom.surface[surf_name].Lcomp = _floats(eval_lines[i])[0]

        elif tline.upper() == "YDUPLICATE":
            i += 1
            geom.surface[surf_name].Ydupl = _floats(eval_lines[i])[0]

        elif tline.upper() == "SCALE":
            i += 1
            geom.surface[surf_name].Scale = _floats(eval_lines[i])

        elif tline.upper() == "TRANSLATE":
            i += 1
            geom.surface[surf_name].Trans = _floats(eval_lines[i])

        elif tline.upper() == "ANGLE":
            i += 1
            geom.surface[surf_name].dAinc = _floats(eval_lines[i])[0]

        elif tline.upper() == "NOWAKE":
            geom.surface[surf_name].NOWAKE = True

        elif tline.upper() == "NOALBE":
            geom.surface[surf_name].NOALBE = True

        elif tline.upper() == "NOLOAD":
            geom.surface[surf_name].NOLOAD = True

        elif tline.upper() == "SECTION":
            ctrl_num = 0
            sect_num += 1
            i += 1
            vals = _floats(eval_lines[i])
            sec = geom.surface[surf_name].SECTION
            sec.Xle.append(vals[0] if len(vals) > 0 else 0.0)
            sec.Yle.append(vals[1] if len(vals) > 1 else 0.0)
            sec.Zle.append(vals[2] if len(vals) > 2 else 0.0)
            sec.Chord.append(vals[3] if len(vals) > 3 else 0.0)
            sec.Ainc.append(vals[4] if len(vals) > 4 else 0.0)
            sec.Nspan.append(vals[5] if len(vals) > 5 else 0.0)
            sec.Sspan.append(vals[6] if len(vals) > 6 else 0.0)
            sec.NACA.append(None)
            sec.Afile.append(None)
            sec.CLaf.append(None)

        elif tline.upper() == "NACA":
            i += 1
            geom.surface[surf_name].SECTION.NACA[sect_num - 1] = eval_lines[i].strip()

        elif tline.upper() in ("AIRFOIL", "DESIGN"):
            pass  # TODO: not yet implemented

        elif tline.upper() == "AFIL":
            i += 1
            geom.surface[surf_name].SECTION.Afile[sect_num - 1] = eval_lines[i].strip()

        elif tline.upper() == "CONTROL":
            ctrl_num += 1
            i += 1
            parts = eval_lines[i].split()
            ctrl = geom.surface[surf_name].CONTROL
            while len(ctrl.Name) < ctrl_num:
                ctrl.Name.append([])
                ctrl.Gain.append([])
                ctrl.Xhinge.append([])
                ctrl.XYZhvec.append([])
                ctrl.SgnDup.append([])
            for lst in (ctrl.Name, ctrl.Gain, ctrl.Xhinge, ctrl.XYZhvec, ctrl.SgnDup):
                while len(lst[ctrl_num - 1]) < sect_num:
                    lst[ctrl_num - 1].append(None)
            ctrl.Name[ctrl_num - 1][sect_num - 1] = parts[0]
            ctrl.Gain[ctrl_num - 1][sect_num - 1] = float(parts[1])
            ctrl.Xhinge[ctrl_num - 1][sect_num - 1] = float(parts[2])
            ctrl.XYZhvec[ctrl_num - 1][sect_num - 1] = float(parts[3])
            if len(parts) < 6:
                raise ValueError(
                    f"CONTROL line has {len(parts)} tokens, expected at least 6 "
                    f"(name gain xhinge XYZhvec[0-2] [SgnDup]): {eval_lines[i]!r}"
                )
            # SgnDup is optional; omitted means +1.0 (positive duplication)
            ctrl.SgnDup[ctrl_num - 1][sect_num - 1] = (
                float(parts[6]) if len(parts) > 6 else 1.0
            )

        elif tline.upper() == "CLAF":
            i += 1
            geom.surface[surf_name].SECTION.CLaf[sect_num - 1] = _floats(eval_lines[i])[
                0
            ]

        i += 1

    return geom
