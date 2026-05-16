"""Tests for aero_fileplot: interactive AeroDatabase surface plots."""

from __future__ import annotations

import plotly.graph_objects as go
import pytest

from avl_aero_tables.aero_fileplot import aero_fileplot
from avl_aero_tables.aero_filewrite import AeroDatabase, aero_filewrite
from avl_aero_tables.avl_fileread import StResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_result(
    alpha: float,
    beta: float,
    deflections: dict[str, float] | None = None,
) -> StResult:
    r = StResult(filename="case.st")
    r.controls = {"d01": "elevator"}
    r.data = {
        "Alpha": alpha,
        "Beta": beta,
        "Sref": 100.0,
        "Cref": 5.0,
        "Bref": 20.0,
        "Xref": 2.0,
        "Yref": 0.0,
        "Zref": 0.0,
        "CLtot": 0.5 + alpha * 0.05,
        "CYtot": 0.0,
        "CDtot": 0.02,
        "Cltot": 0.0,
        "Cmtot": -0.05,
        "Cntot": 0.0,
        "elevator": 0.0,
    }
    if deflections:
        r.data.update(deflections)
    return r


def _minimal_aero() -> AeroDatabase:
    results = [_make_result(a, 0.0) for a in [-5.0, 0.0, 5.0]]
    return aero_filewrite(results)


def _ctrl_aero() -> AeroDatabase:
    results = [
        _make_result(a, 0.0, deflections={"elevator": d})
        for a in [-5.0, 0.0, 5.0]
        for d in [-10.0, 0.0, 10.0]
    ]
    return aero_filewrite(results)


# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-1")
def test_returns_list():
    figs = aero_fileplot(_minimal_aero())
    assert isinstance(figs, list)


@pytest.mark.req("req-aeroplot-2")
def test_returns_plotly_figures():
    figs = aero_fileplot(_minimal_aero())
    for f in figs:
        assert isinstance(f, go.Figure)


# ---------------------------------------------------------------------------
# Stability figure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-3")
def test_stability_figure_first():
    figs = aero_fileplot(_minimal_aero())
    assert len(figs) >= 1
    # Stability figure has 6 Surface traces (one per coef)
    surfaces = [t for t in figs[0].data if isinstance(t, go.Surface)]
    assert len(surfaces) == 6


@pytest.mark.req("req-aeroplot-4")
def test_stability_subplot_titles():
    figs = aero_fileplot(_minimal_aero())
    titles = {a.text for a in figs[0].layout.annotations}
    assert "CLtot" in titles
    assert "CDtot" in titles


# ---------------------------------------------------------------------------
# No control surfaces → only stability figure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-5")
def test_no_ctrl_only_stability_figure():
    r = StResult(filename="bare.st")
    r.controls = {}
    r.data = {
        "Alpha": 0.0, "Beta": 0.0,
        "CLtot": 0.5, "CYtot": 0.0, "CDtot": 0.02,
        "Cltot": 0.0, "Cmtot": -0.05, "Cntot": 0.0,
    }
    figs = aero_fileplot(aero_filewrite([r]))
    assert len(figs) == 1


# ---------------------------------------------------------------------------
# Control figures
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-6")
def test_ctrl_figures_produced():
    figs = aero_fileplot(_ctrl_aero())
    assert len(figs) == 7  # stability + 6 coef ctrl figures


@pytest.mark.req("req-aeroplot-7")
def test_ctrl_figure_has_one_surface_per_control():
    figs = aero_fileplot(_ctrl_aero())
    ctrl_fig = figs[1]
    surfaces = [t for t in ctrl_fig.data if isinstance(t, go.Surface)]
    assert len(surfaces) == 1  # one surface (elevator only)


@pytest.mark.req("req-aeroplot-8")
def test_ctrl_figure_titles_contain_coef_name():
    figs = aero_fileplot(_ctrl_aero())
    for f in figs[1:]:
        assert any(
            c in f.layout.title.text
            for c in ("CLtot", "CYtot", "CDtot", "Cltot", "Cmtot", "Cntot")
        )


# ---------------------------------------------------------------------------
# beta_ref selection
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-9")
def test_beta_ref_nearest_used():
    results = [_make_result(0.0, b) for b in [-5.0, 0.0, 5.0]]
    figs = aero_fileplot(aero_filewrite(results), beta_ref=1.0)
    assert len(figs) >= 1
