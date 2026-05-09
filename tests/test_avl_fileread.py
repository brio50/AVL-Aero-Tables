import warnings
from pathlib import Path

import pytest

from avl_wrapper.avl_fileread import avl_fileread

AVL_DIR = Path(__file__).parent.parent / "examples"
ALL_AVL_FILES = sorted(AVL_DIR.glob("*.avl"))


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


def test_bubble_dancer_surfaces():
    g = avl_fileread(AVL_DIR / "bd.avl")
    assert set(g.surface.keys()) == {"Wing", "Horizontal_tail", "Vertical_tail"}


def test_bubble_dancer_wing_sections():
    g = avl_fileread(AVL_DIR / "bd.avl")
    wing = g.surface["Wing"]
    assert wing.Nchord == pytest.approx(6.0)
    assert wing.Ydupl == pytest.approx(0.0)
    sec = wing.SECTION
    assert len(sec.Xle) == 6
    assert sec.Xle == pytest.approx([-3.41, -3.25, -2.5, -1.788, -0.95, 0.0])
    assert sec.Yle == pytest.approx([0.0, 18.0, 41.66, 55.75, 57.64, 58.3])
    assert sec.Chord == pytest.approx([10.5, 10.0, 8.0, 5.5, 4.4, 3.375])


def test_bubble_dancer_controls():
    g = avl_fileread(AVL_DIR / "bd.avl")
    wing_ctrl = g.surface["Wing"].CONTROL
    assert wing_ctrl.Name[0][0] == "flap"
    assert wing_ctrl.Name[0][4] == "aileron"

    htail_ctrl = g.surface["Horizontal_tail"].CONTROL
    assert htail_ctrl.Name[0][0] == "elevator"

    vtail_ctrl = g.surface["Vertical_tail"].CONTROL
    assert vtail_ctrl.Name[0][0] == "rudder"


def test_bubble_dancer_body():
    g = avl_fileread(AVL_DIR / "bd.avl")
    assert g.body is not None
    assert g.body.Trans == pytest.approx([-12.5, 0.0, -1.4])


@pytest.mark.parametrize("avl_file", ALL_AVL_FILES, ids=lambda p: p.name)
def test_all_avl_files_parse(avl_file):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        g = avl_fileread(avl_file)
    assert g.header.name != ""
    assert isinstance(g.surface, dict)
