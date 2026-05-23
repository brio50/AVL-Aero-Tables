from pathlib import Path

import pandas as pd
import pytest

from avl_aero_tables.aero_filewrite import results_to_dataframe
from avl_aero_tables.avl_fileread import st_fileread

FIXTURES = Path(__file__).parent.parent / "examples" / "bd"


@pytest.mark.req("req-stab-1")
def test_single_file_returns_one_result():
    results = st_fileread(FIXTURES / "bd_alpha5_beta0.st")
    assert len(results) == 1


@pytest.mark.req("req-stab-2")
def test_filename():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.filename == "bd_alpha5_beta0.st"


@pytest.mark.req("req-stab-3")
def test_controls():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.controls == {
        "d01": "flap",
        "d02": "aileron",
        "d03": "elevator",
        "d04": "rudder",
    }


@pytest.mark.req("req-stab-4")
def test_flight_condition_scalars():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["Alpha"] == pytest.approx(5.0)
    assert r.data["Beta"] == pytest.approx(0.0)
    assert r.data["Mach"] == pytest.approx(0.0)


@pytest.mark.req("req-stab-5")
def test_total_forces():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["CLtot"] == pytest.approx(0.58447)
    assert r.data["CDtot"] == pytest.approx(0.02526)
    assert r.data["CDvis"] == pytest.approx(0.01700)


@pytest.mark.req("req-stab-6")
def test_stability_derivatives():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["CLa"] == pytest.approx(5.631072)
    assert r.data["CLb"] == pytest.approx(-0.000000, abs=1e-6)
    assert r.data["Cma"] == pytest.approx(-0.938373)
    assert r.data["Cmq"] == pytest.approx(-12.174270)
    assert r.data["Cnb"] == pytest.approx(0.061288)


@pytest.mark.req("req-stab-7")
def test_control_derivatives():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["CLd01"] == pytest.approx(0.019376)
    assert r.data["CLd03"] == pytest.approx(0.008018)
    assert r.data["Cmd03"] == pytest.approx(-0.027294)


@pytest.mark.req("req-stab-8")
def test_neutral_point():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["Xnp"] == pytest.approx(5.066419)


@pytest.mark.req("req-stab-9")
def test_spiral_stability():
    r = st_fileread(FIXTURES / "bd_alpha5_beta0.st")[0]
    assert r.data["Clb_Cnr_div_Clr_Cnb"] == pytest.approx(1.681007)
    assert r.data["Cnb"] == pytest.approx(0.061288)


@pytest.mark.req("req-stab-10")
def test_directory_read():
    results = st_fileread(FIXTURES)
    assert len(results) == 1  # only one .st fixture currently
    assert results[0].filename == "bd_alpha5_beta0.st"


# ---------------------------------------------------------------------------
# results_to_dataframe
# ---------------------------------------------------------------------------


@pytest.mark.req("req-stab-11")
def test_results_to_dataframe_returns_dataframe():
    results = st_fileread(FIXTURES / "bd_alpha5_beta0.st")
    df = results_to_dataframe(results)
    assert isinstance(df, pd.DataFrame)


@pytest.mark.req("req-stab-11")
def test_results_to_dataframe_one_row_per_result():
    results = st_fileread(FIXTURES / "bd_alpha5_beta0.st")
    df = results_to_dataframe(results)
    assert len(df) == len(results)


@pytest.mark.req("req-stab-12")
def test_results_to_dataframe_columns_include_filename_and_data():
    results = st_fileread(FIXTURES / "bd_alpha5_beta0.st")
    df = results_to_dataframe(results)
    assert "filename" in df.columns
    assert "Alpha" in df.columns
    assert "CLtot" in df.columns


@pytest.mark.req("req-stab-13")
def test_results_to_dataframe_values():
    results = st_fileread(FIXTURES / "bd_alpha5_beta0.st")
    df = results_to_dataframe(results)
    assert df["Alpha"].iloc[0] == pytest.approx(5.0)
    assert df["CLtot"].iloc[0] == pytest.approx(0.58447)
    assert df["filename"].iloc[0] == "bd_alpha5_beta0.st"
