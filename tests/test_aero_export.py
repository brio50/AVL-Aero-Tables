"""Tests for aero_to_mat / aero_to_hdf5: exporting AeroDatabase to .mat/.h5."""

from __future__ import annotations

import h5py
import numpy as np
import pytest
import scipy.io as scipy_io
from test_aero_filewrite import CTRL_MAP, _make_result

from avl_aero_tables.aero_filewrite import aero_filewrite, aero_to_hdf5, aero_to_mat

# ---------------------------------------------------------------------------
# Fixture database
# ---------------------------------------------------------------------------


def _make_db():
    results = [
        _make_result(
            a, b, coef_vals={"CLtot": a * 0.1 + b * 0.01}, deflections={"flap": d}
        )
        for a in [-5.0, 0.0, 5.0]
        for b in [-3.0, 0.0, 3.0]
        for d in [-5.0, 0.0, 5.0]
    ]
    return aero_filewrite(results)


# ---------------------------------------------------------------------------
# aero_to_mat
# ---------------------------------------------------------------------------


@pytest.mark.req("req-export-1")
def test_aero_to_mat_writes_file(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    assert path.exists()


@pytest.mark.req("req-export-2")
def test_aero_to_mat_top_level_scalars(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    out = scipy_io.loadmat(path, simplify_cells=True)
    assert out["date"] == db.date
    assert out["Sref"] == pytest.approx(db.Sref)
    assert out["Cref"] == pytest.approx(db.Cref)
    assert out["Xref"] == pytest.approx(db.Xref)


@pytest.mark.req("req-export-3")
def test_aero_to_mat_breakpoints(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    out = scipy_io.loadmat(path, simplify_cells=True)
    np.testing.assert_array_equal(
        out["breakpoints"]["alpha"], db.total_stab["CLtot"].alpha
    )
    np.testing.assert_array_equal(
        out["breakpoints"]["beta"], db.total_stab["CLtot"].beta
    )
    np.testing.assert_array_equal(
        out["breakpoints"]["defl"]["d01_flap"],
        db.total_ctrl["CLtot_d01_flap"].defl,
    )


@pytest.mark.req("req-export-4")
def test_aero_to_mat_stab_table_values(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    out = scipy_io.loadmat(path, simplify_cells=True)
    np.testing.assert_allclose(
        out["stab"]["CLtot"], db.total_stab["CLtot"].data, equal_nan=True
    )


@pytest.mark.req("req-export-5")
def test_aero_to_mat_ctrl_table_values_and_shape(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    out = scipy_io.loadmat(path, simplify_cells=True)
    mat_data = out["ctrl"]["d01_flap"]["CLtot"]
    expected = db.total_ctrl["CLtot_d01_flap"].data
    assert mat_data.shape == expected.shape
    np.testing.assert_allclose(mat_data, expected, equal_nan=True)


@pytest.mark.req("req-export-6")
def test_aero_to_mat_stab_deriv_and_ctrl_deriv_included(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.mat"
    aero_to_mat(db, path)
    out = scipy_io.loadmat(path, simplify_cells=True)
    np.testing.assert_allclose(
        out["stab_deriv"]["CLa"], db.stab_deriv["CLa"].data, equal_nan=True
    )
    np.testing.assert_allclose(
        out["ctrl_deriv"]["CL_d01_flap"],
        db.ctrl_deriv["CL_d01_flap"].data,
        equal_nan=True,
    )


@pytest.mark.req("req-export-7")
def test_aero_to_mat_accepts_str_path(tmp_path):
    db = _make_db()
    path = str(tmp_path / "aero_str.mat")
    aero_to_mat(db, path)
    import os

    assert os.path.exists(path)


# ---------------------------------------------------------------------------
# aero_to_hdf5
# ---------------------------------------------------------------------------


@pytest.mark.req("req-export-8")
def test_aero_to_hdf5_writes_file(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    assert path.exists()


@pytest.mark.req("req-export-9")
def test_aero_to_hdf5_top_level_scalars(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    with h5py.File(path, "r") as f:
        assert f["date"][()].decode() == db.date
        assert f["Sref"][()] == pytest.approx(db.Sref)
        assert f["Xref"][()] == pytest.approx(db.Xref)


@pytest.mark.req("req-export-10")
def test_aero_to_hdf5_breakpoints(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    with h5py.File(path, "r") as f:
        np.testing.assert_array_equal(
            f["breakpoints/alpha"][()], db.total_stab["CLtot"].alpha
        )
        np.testing.assert_array_equal(
            f["breakpoints/beta"][()], db.total_stab["CLtot"].beta
        )
        np.testing.assert_array_equal(
            f["breakpoints/defl/d01_flap"][()],
            db.total_ctrl["CLtot_d01_flap"].defl,
        )


@pytest.mark.req("req-export-11")
def test_aero_to_hdf5_stab_table_values(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    with h5py.File(path, "r") as f:
        np.testing.assert_allclose(
            f["stab/CLtot"][()], db.total_stab["CLtot"].data, equal_nan=True
        )


@pytest.mark.req("req-export-12")
def test_aero_to_hdf5_ctrl_table_hierarchy_and_values(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    with h5py.File(path, "r") as f:
        for d_idx, ctrl_name in CTRL_MAP.items():
            surf = f"{d_idx}_{ctrl_name}"
            for coef in ("CLtot", "CYtot", "CDtot", "Cltot", "Cmtot", "Cntot"):
                assert f"ctrl/{surf}/{coef}" in f
        data = f["ctrl/d01_flap/CLtot"][()]
        expected = db.total_ctrl["CLtot_d01_flap"].data
        assert data.shape == expected.shape
        np.testing.assert_allclose(data, expected, equal_nan=True)


@pytest.mark.req("req-export-13")
def test_aero_to_hdf5_stab_deriv_and_ctrl_deriv_included(tmp_path):
    db = _make_db()
    path = tmp_path / "aero.h5"
    aero_to_hdf5(db, path)
    with h5py.File(path, "r") as f:
        np.testing.assert_allclose(
            f["stab_deriv/CLa"][()], db.stab_deriv["CLa"].data, equal_nan=True
        )
        np.testing.assert_allclose(
            f["ctrl_deriv/CL_d01_flap"][()],
            db.ctrl_deriv["CL_d01_flap"].data,
            equal_nan=True,
        )


@pytest.mark.req("req-export-14")
def test_aero_to_hdf5_accepts_str_path(tmp_path):
    db = _make_db()
    path = str(tmp_path / "aero_str.h5")
    aero_to_hdf5(db, path)
    import os

    assert os.path.exists(path)
