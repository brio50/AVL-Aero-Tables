"""Tests for aero_filewrite: pivoting StResult lists into AeroDatabase tables."""

from __future__ import annotations

import numpy as np
import pytest

from avl_aero_tables.aero_filewrite import (
    COEF_NAMES,
    AeroDatabase,
    CtrlTable,
    StabTable,
    aero_filewrite,
)
from avl_aero_tables.avl_fileread import StResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CTRL_MAP = {"d01": "flap", "d02": "aileron"}


def _make_result(
    alpha: float,
    beta: float,
    coef_vals: dict[str, float] | None = None,
    deflections: dict[str, float] | None = None,
) -> StResult:
    r = StResult(filename="case.st")
    r.controls = dict(CTRL_MAP)
    r.data = {
        "Alpha": alpha,
        "Beta": beta,
        "Sref": 1000.0,
        "Cref": 10.0,
        "Bref": 116.6,
        "Xref": 3.4,
        "Yref": 0.0,
        "Zref": 0.5,
        "CLtot": 0.5,
        "CYtot": 0.0,
        "CDtot": 0.03,
        "Cltot": 0.0,
        "Cmtot": -0.1,
        "Cntot": 0.0,
        "flap": 0.0,
        "aileron": 0.0,
    }
    if coef_vals:
        r.data.update(coef_vals)
    if deflections:
        r.data.update(deflections)
    return r


# ---------------------------------------------------------------------------
# Single result — structure checks
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-1")
def test_returns_aero_database():
    db = aero_filewrite([_make_result(5.0, 0.0)])
    assert isinstance(db, AeroDatabase)


@pytest.mark.req("req-write-3")
def test_date_is_set():
    db = aero_filewrite([_make_result(5.0, 0.0)])
    assert db.date != ""


@pytest.mark.req("req-write-4")
def test_ref_fields_populated():
    db = aero_filewrite([_make_result(5.0, 0.0)])
    assert db.Sref == pytest.approx(1000.0)
    assert db.Cref == pytest.approx(10.0)
    assert db.Xref == pytest.approx(3.4)


@pytest.mark.req("req-write-5")
def test_stab_tables_created_for_all_coefs():
    db = aero_filewrite([_make_result(5.0, 0.0)])
    for coef in COEF_NAMES:
        assert coef in db.stab
        assert isinstance(db.stab[coef], StabTable)


@pytest.mark.req("req-write-6")
def test_ctrl_tables_created_for_each_coef_surface():
    db = aero_filewrite([_make_result(5.0, 0.0)])
    for coef in COEF_NAMES:
        for d_idx, ctrl_name in CTRL_MAP.items():
            key = f"{coef}_{d_idx}_{ctrl_name}"
            assert key in db.ctrl
            assert isinstance(db.ctrl[key], CtrlTable)


# ---------------------------------------------------------------------------
# Breakpoints
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-7")
def test_alpha_breakpoints_sorted():
    results = [_make_result(a, 0.0) for a in [5.0, -5.0, 0.0]]
    db = aero_filewrite(results)
    np.testing.assert_array_equal(db.stab["CLtot"].alpha, [-5.0, 0.0, 5.0])


@pytest.mark.req("req-write-8")
def test_beta_breakpoints_sorted():
    results = [_make_result(0.0, b) for b in [3.0, -3.0, 0.0]]
    db = aero_filewrite(results)
    np.testing.assert_array_equal(db.stab["CLtot"].beta, [-3.0, 0.0, 3.0])


@pytest.mark.req("req-write-9")
def test_stab_table_shape():
    results = [_make_result(a, b) for a in [-5.0, 0.0, 5.0] for b in [-3.0, 0.0, 3.0]]
    db = aero_filewrite(results)
    assert db.stab["CLtot"].data.shape == (3, 3)


# ---------------------------------------------------------------------------
# Stability table — neutral cases
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-10")
def test_neutral_case_fills_stab_table():
    r = _make_result(5.0, 0.0, coef_vals={"CLtot": 0.58})
    db = aero_filewrite([r])
    assert db.stab["CLtot"].data[0, 0] == pytest.approx(0.58)


@pytest.mark.req("req-write-11")
def test_non_neutral_does_not_fill_stab_table():
    r = _make_result(5.0, 0.0, deflections={"flap": 10.0})
    db = aero_filewrite([r])
    assert np.isnan(db.stab["CLtot"].data[0, 0])


@pytest.mark.req("req-write-9", "req-write-10")
def test_multiple_alphas_stab_shape_and_values():
    results = [
        _make_result(a, 0.0, coef_vals={"CLtot": a * 0.1}) for a in [-5.0, 0.0, 5.0]
    ]
    db = aero_filewrite(results)
    assert db.stab["CLtot"].data.shape == (3, 1)
    np.testing.assert_allclose(db.stab["CLtot"].data[:, 0], [-0.5, 0.0, 0.5], atol=1e-9)


# ---------------------------------------------------------------------------
# Control table
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-13")
def test_ctrl_table_defl_breakpoints():
    results = [
        _make_result(0.0, 0.0, deflections={"flap": d}) for d in [-5.0, 0.0, 5.0]
    ]
    db = aero_filewrite(results)
    key = "CLtot_d01_flap"
    np.testing.assert_array_equal(db.ctrl[key].defl, [-5.0, 0.0, 5.0])


@pytest.mark.req("req-write-12")
def test_ctrl_table_shape():
    results = [
        _make_result(a, 0.0, deflections={"flap": d})
        for a in [0.0, 5.0]
        for d in [-5.0, 0.0, 5.0]
    ]
    db = aero_filewrite(results)
    assert db.ctrl["CLtot_d01_flap"].data.shape == (2, 1, 3)


@pytest.mark.req("req-write-14")
def test_ctrl_table_values_filled():
    results = [
        _make_result(0.0, 0.0, coef_vals={"CLtot": v}, deflections={"flap": d})
        for d, v in [(-5.0, 0.4), (0.0, 0.5), (5.0, 0.6)]
    ]
    db = aero_filewrite(results)
    np.testing.assert_allclose(
        db.ctrl["CLtot_d01_flap"].data[0, 0, :], [0.4, 0.5, 0.6], atol=1e-9
    )


@pytest.mark.req("req-write-15")
def test_ctrl_table_surface_and_ctrl_name():
    db = aero_filewrite([_make_result(0.0, 0.0)])
    t = db.ctrl["CLtot_d01_flap"]
    assert t.surface == "d01_flap"
    assert t.ctrl_name == "flap"


# ---------------------------------------------------------------------------
# No control surfaces
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-16")
def test_no_controls_empty_ctrl_dict():
    r = StResult(filename="bare.st")
    r.controls = {}
    r.data = {
        "Alpha": 0.0,
        "Beta": 0.0,
        "CLtot": 0.5,
        "CYtot": 0.0,
        "CDtot": 0.02,
        "Cltot": 0.0,
        "Cmtot": -0.1,
        "Cntot": 0.0,
    }
    db = aero_filewrite([r])
    assert db.ctrl == {}


@pytest.mark.req("req-write-17")
def test_no_controls_stab_table_filled():
    r = StResult(filename="bare.st")
    r.controls = {}
    r.data = {
        "Alpha": 0.0,
        "Beta": 0.0,
        "CLtot": 0.42,
        "CYtot": 0.0,
        "CDtot": 0.02,
        "Cltot": 0.0,
        "Cmtot": -0.1,
        "Cntot": 0.0,
    }
    db = aero_filewrite([r])
    assert db.stab["CLtot"].data[0, 0] == pytest.approx(0.42)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.req("req-write-2")
def test_empty_results_raises():
    with pytest.raises(ValueError, match="empty"):
        aero_filewrite([])


@pytest.mark.req("req-write-18")
def test_missing_coef_produces_nan():
    r = _make_result(0.0, 0.0)
    del r.data["CDtot"]
    db = aero_filewrite([r])
    assert np.isnan(db.stab["CDtot"].data[0, 0])
