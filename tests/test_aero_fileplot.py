"""Tests for aero_fileplot: plotting AeroDatabase tables."""

from __future__ import annotations

import matplotlib
import pytest

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from avl_aero_tables.aero_fileplot import aero_fileplot
from avl_aero_tables.aero_filewrite import (
    AeroDatabase,
    aero_filewrite,
)
from avl_aero_tables.st_fileread import StResult

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
    """AeroDatabase with alpha sweep, one beta, no ctrl sweep."""
    results = [_make_result(a, 0.0) for a in [-5.0, 0.0, 5.0]]
    return aero_filewrite(results)


def _ctrl_aero() -> AeroDatabase:
    """AeroDatabase with alpha sweep and elevator deflection sweep."""
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
    aero = _minimal_aero()
    figs = aero_fileplot(aero)
    assert isinstance(figs, list)
    for f in figs:
        plt.close(f)


@pytest.mark.req("req-aeroplot-2")
def test_returns_figures():
    aero = _minimal_aero()
    figs = aero_fileplot(aero)
    for f in figs:
        assert isinstance(f, plt.Figure)
    for f in figs:
        plt.close(f)


# ---------------------------------------------------------------------------
# Stability figure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-3")
def test_stability_figure_first():
    aero = _minimal_aero()
    figs = aero_fileplot(aero)
    assert len(figs) >= 1
    # First figure has 6 subplots (one per coef)
    assert len(figs[0].axes) == 6
    for f in figs:
        plt.close(f)


@pytest.mark.req("req-aeroplot-4")
def test_stability_axes_titles():
    aero = _minimal_aero()
    figs = aero_fileplot(aero)
    titles = {ax.get_title() for ax in figs[0].axes}
    assert "CLtot" in titles
    assert "CDtot" in titles
    for f in figs:
        plt.close(f)


# ---------------------------------------------------------------------------
# No control surfaces → only stability figure
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-5")
def test_no_ctrl_only_stability_figure():
    r = StResult(filename="bare.st")
    r.controls = {}
    r.data = {
        "Alpha": 0.0,
        "Beta": 0.0,
        "CLtot": 0.5,
        "CYtot": 0.0,
        "CDtot": 0.02,
        "Cltot": 0.0,
        "Cmtot": -0.05,
        "Cntot": 0.0,
    }
    aero = aero_filewrite([r])
    figs = aero_fileplot(aero)
    assert len(figs) == 1  # only stability figure
    plt.close(figs[0])


# ---------------------------------------------------------------------------
# Control figures
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-6")
def test_ctrl_figures_produced():
    aero = _ctrl_aero()
    figs = aero_fileplot(aero)
    # stability + 6 coef ctrl figures
    assert len(figs) == 7
    for f in figs:
        plt.close(f)


@pytest.mark.req("req-aeroplot-7")
def test_ctrl_figure_has_one_subplot_per_surface():
    aero = _ctrl_aero()
    figs = aero_fileplot(aero)
    # First ctrl figure (index 1): one subplot per surface (only elevator here)
    ctrl_fig = figs[1]
    assert len(ctrl_fig.axes) == 1  # one surface
    for f in figs:
        plt.close(f)


@pytest.mark.req("req-aeroplot-8")
def test_ctrl_figure_title_contains_coef_name():
    aero = _ctrl_aero()
    figs = aero_fileplot(aero)
    ctrl_titles = [f.texts[0].get_text() for f in figs[1:]]
    # each ctrl figure title should contain a coefficient name
    for title in ctrl_titles:
        assert any(
            c in title for c in ("CLtot", "CYtot", "CDtot", "Cltot", "Cmtot", "Cntot")
        )
    for f in figs:
        plt.close(f)


# ---------------------------------------------------------------------------
# beta_ref selection
# ---------------------------------------------------------------------------


@pytest.mark.req("req-aeroplot-9")
def test_beta_ref_nearest_used():
    """aero_fileplot should not crash if beta_ref is not exact."""
    results = [_make_result(0.0, b) for b in [-5.0, 0.0, 5.0]]
    aero = aero_filewrite(results)
    figs = aero_fileplot(aero, beta_ref=1.0)  # nearest is 0.0
    assert len(figs) >= 1
    for f in figs:
        plt.close(f)
