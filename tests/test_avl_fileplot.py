"""Tests for avl_fileplot: interactive geometry visualization."""

from pathlib import Path

import plotly.graph_objects as go
import pytest

from avl_aero_tables.avl_fileplot import avl_fileplot
from avl_aero_tables.avl_fileread import avl_fileread

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_AVL = EXAMPLES / "bd" / "bd.avl"
PLANE_AVL = EXAMPLES / "plane" / "plane.avl"


# ---------------------------------------------------------------------------
# Return type and figure structure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-1")
def test_returns_figure():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert isinstance(fig, go.Figure)


@pytest.mark.req("req-plot-2")
def test_figure_has_one_scene():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    scenes = [k for k in fig.layout.to_plotly_json() if k.startswith("scene")]
    assert len(scenes) == 1


@pytest.mark.req("req-plot-3")
def test_all_traces_are_scatter3d_or_cone():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert all(isinstance(t, (go.Scatter3d, go.Cone)) for t in fig.data)


@pytest.mark.req("req-plot-5")
def test_figure_title_contains_geometry_name():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert geom.header.name in fig.layout.title.text


# ---------------------------------------------------------------------------
# Geometry content
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-6")
def test_line_traces_drawn(bd_geometry):
    fig = avl_fileplot(bd_geometry)
    line_traces = [t for t in fig.data if isinstance(t, go.Scatter3d) and t.mode == "lines"]
    assert len(line_traces) > 0


@pytest.mark.req("req-plot-7")
def test_cg_marker_present(bd_geometry):
    fig = avl_fileplot(bd_geometry)
    marker_traces = [t for t in fig.data if isinstance(t, go.Scatter3d) and t.mode == "markers"]
    assert len(marker_traces) > 0


def test_body_geometry_runs(bd_geometry):
    """bd.avl has a body; must plot without error."""
    fig = avl_fileplot(bd_geometry)
    assert isinstance(fig, go.Figure)


@pytest.mark.req("req-plot-8")
def test_no_body_geometry_no_crash():
    """plane.avl has no body; should plot surfaces only."""
    geom = avl_fileread(PLANE_AVL)
    fig = avl_fileplot(geom)
    assert isinstance(fig, go.Figure)


# ---------------------------------------------------------------------------
# Mirror symmetry
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-9")
def test_mirror_doubles_traces(bd_geometry):
    """bd.avl has Ydupl=0 surfaces; mirrored traces should be present."""
    fig = avl_fileplot(bd_geometry)
    line_traces = [t for t in fig.data if isinstance(t, go.Scatter3d) and t.mode == "lines"]
    assert len(line_traces) >= 4


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bd_geometry():
    return avl_fileread(BD_AVL)
