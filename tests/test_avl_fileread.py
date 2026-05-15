import warnings
from pathlib import Path

import pytest

from avl_aero_tables.avl_fileread import avl_fileread

AVL_DIR = Path(__file__).parent.parent / "examples"
ALL_AVL_FILES = sorted(AVL_DIR.glob("*.avl"))


@pytest.mark.req("req-geom-2")
def test_bubble_dancer_header():
    g = avl_fileread(AVL_DIR / "bd.avl")
    h = g.header
    assert h.name == "Bubble Dancer RES"
    assert h.Mach == 0.0
    assert h.iYsym == 0
    assert h.iZsym == 0
    assert h.Zsym == 0.0
    assert h.Sref == pytest.approx(1000.0)
    assert h.Cref == pytest.approx(10.0)
    assert h.Bref == pytest.approx(116.6)
    assert h.Xref == pytest.approx(3.4)
    assert h.Yref == pytest.approx(0.0)
    assert h.Zref == pytest.approx(0.5)
    assert h.CDoref == pytest.approx(0.017)


@pytest.mark.req("req-geom-3")
def test_bubble_dancer_surfaces():
    g = avl_fileread(AVL_DIR / "bd.avl")
    assert set(g.surface.keys()) == {"Wing", "Horizontal_tail", "Vertical_tail"}


@pytest.mark.req("req-geom-4")
def test_bubble_dancer_wing_sections():
    g = avl_fileread(AVL_DIR / "bd.avl")
    wing = g.surface["Wing"]
    assert wing.nchord == pytest.approx(6.0)
    assert wing.ydupl == pytest.approx(0.0)
    assert len(wing.sections) == 6
    assert [s.xle for s in wing.sections] == pytest.approx(
        [-3.41, -3.25, -2.5, -1.788, -0.95, 0.0]
    )
    assert [s.yle for s in wing.sections] == pytest.approx(
        [0.0, 18.0, 41.66, 55.75, 57.64, 58.3]
    )
    assert [s.chord for s in wing.sections] == pytest.approx(
        [10.5, 10.0, 8.0, 5.5, 4.4, 3.375]
    )


@pytest.mark.req("req-geom-5")
def test_bubble_dancer_controls():
    g = avl_fileread(AVL_DIR / "bd.avl")
    wing = g.surface["Wing"]
    assert wing.sections[0].controls[0].name == "flap"
    assert wing.sections[4].controls[0].name == "aileron"

    htail = g.surface["Horizontal_tail"]
    assert htail.sections[0].controls[0].name == "elevator"

    vtail = g.surface["Vertical_tail"]
    assert vtail.sections[0].controls[0].name == "rudder"


@pytest.mark.req("req-geom-6")
def test_bubble_dancer_body():
    g = avl_fileread(AVL_DIR / "bd.avl")
    assert g.body is not None
    assert g.body.trans == pytest.approx([-12.5, 0.0, -1.4])


@pytest.mark.req("req-geom-1")
@pytest.mark.parametrize("avl_file", ALL_AVL_FILES, ids=lambda p: p.name)
def test_all_avl_files_parse(avl_file):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        g = avl_fileread(avl_file)
    assert g.header.name != ""
    assert isinstance(g.surface, dict)
