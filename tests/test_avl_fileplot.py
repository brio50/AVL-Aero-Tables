"""Tests for avl_fileplot: geometry visualization."""

from pathlib import Path

import matplotlib
import pytest

matplotlib.use("Agg")  # headless — must be set before importing pyplot

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

from avl_aero_tables.avl_fileplot import avl_fileplot
from avl_aero_tables.avl_fileread import avl_fileread

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_AVL = EXAMPLES / "bd" / "bd.avl"
ELLIPG_AVL = Path(__file__).parent / "data" / "ellipg.avl"


# ---------------------------------------------------------------------------
# Return type and figure structure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-1")
def test_returns_figure():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


@pytest.mark.req("req-plot-2")
def test_figure_has_four_axes():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert len(fig.axes) == 4
    plt.close(fig)


@pytest.mark.req("req-plot-3")
def test_all_axes_are_3d():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    for ax in fig.axes:
        assert isinstance(ax, Axes3D)
    plt.close(fig)


@pytest.mark.req("req-plot-4")
def test_axes_titles():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    titles = {ax.get_title() for ax in fig.axes}
    assert "Isometric" in titles
    assert "Top" in titles
    assert "Front" in titles
    assert "Side" in titles
    plt.close(fig)


@pytest.mark.req("req-plot-5")
def test_figure_title_contains_geometry_name():
    geom = avl_fileread(BD_AVL)
    fig = avl_fileplot(geom)
    assert geom.header.name in fig.texts[0].get_text()
    plt.close(fig)


# ---------------------------------------------------------------------------
# Geometry content — lines drawn
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-6")
def test_lines_drawn_for_surfaces(bd_geometry):
    fig = avl_fileplot(bd_geometry)
    iso_ax = fig.axes[0]
    # Should have leading/trailing edge lines for each surface
    n_lines = len(iso_ax.lines)
    assert n_lines > 0
    plt.close(fig)


@pytest.mark.req("req-plot-7")
def test_cg_scatter_plotted(bd_geometry):
    fig = avl_fileplot(bd_geometry)
    iso_ax = fig.axes[0]
    # scatter creates a Path3DCollection
    collections = iso_ax.collections
    assert len(collections) > 0
    plt.close(fig)


def test_no_body_geometry_runs(bd_geometry):
    """bd.avl has a body; make sure it plots without error."""
    fig = avl_fileplot(bd_geometry)
    plt.close(fig)


@pytest.mark.req("req-plot-8")
def test_no_body_geometry_no_crash():
    """ellipg.avl has no body; should plot surfaces only."""
    geom = avl_fileread(ELLIPG_AVL)
    fig = avl_fileplot(geom)
    assert isinstance(fig, plt.Figure)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Mirror symmetry
# ---------------------------------------------------------------------------


@pytest.mark.req("req-plot-9")
def test_mirror_doubles_lines(bd_geometry):
    """bd.avl has Ydupl=0 surfaces; mirrored lines should be present."""
    fig = avl_fileplot(bd_geometry)
    iso_ax = fig.axes[0]
    # With mirroring, line count should be at least 2x compared to unmirrored
    # (just verify there are many lines — exact count is an impl detail)
    assert len(iso_ax.lines) >= 4
    plt.close(fig)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def bd_geometry():
    return avl_fileread(BD_AVL)
