"""Tests for avl_sweep: orchestration of AVL sweep runs."""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avl_aero_tables.avl_fileread import StResult, avl_fileread
from avl_aero_tables.avl_sweep import run

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_AVL = EXAMPLES / "bd" / "bd.avl"
BD_MASS = EXAMPLES / "bd" / "bd.mass"


# ---------------------------------------------------------------------------
# ctrl_names property (replaces _extract_ctrl_names)
# ---------------------------------------------------------------------------


@pytest.mark.req("req-geom-7")
def test_ctrl_names_bd():
    geometry = avl_fileread(BD_AVL)
    names = geometry.ctrl_names
    assert "flap" in names
    assert "aileron" in names
    assert "elevator" in names
    assert "rudder" in names


@pytest.mark.req("req-geom-9")
def test_ctrl_names_order_stable():
    geometry = avl_fileread(BD_AVL)
    assert geometry.ctrl_names == geometry.ctrl_names


@pytest.mark.req("req-geom-8")
def test_ctrl_names_no_controls():
    geometry = avl_fileread(EXAMPLES / "ellipg" / "ellipg.avl")
    assert geometry.ctrl_names == []


# ---------------------------------------------------------------------------
# run() — unit tests (subprocess mocked)
# ---------------------------------------------------------------------------


def _make_mock_result(returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stdout = ""
    m.stderr = ""
    return m


@pytest.mark.req("req-sweep-1")
def test_run_calls_avl_runner(tmp_path):
    mock_result = _make_mock_result()
    with patch(
        "avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result
    ) as mock_run:
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)
    mock_run.assert_called_once()


@pytest.mark.req("req-sweep-2")
def test_run_passes_avl_dir_as_cwd(tmp_path):
    mock_result = _make_mock_result()
    with patch(
        "avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result
    ) as mock_run:
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)
    _, kwargs = mock_run.call_args
    assert kwargs["cwd"] == BD_AVL.parent


@pytest.mark.req("req-sweep-3")
def test_run_creates_subdir_inside_out_dir(tmp_path):
    mock_result = _make_mock_result()
    with patch("avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result):
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)
    subdirs = list(tmp_path.iterdir())
    assert len(subdirs) == 1 and subdirs[0].is_dir()


@pytest.mark.req("req-sweep-4")
def test_run_subdir_named_avl_stem_timestamp(tmp_path):
    mock_result = _make_mock_result()
    with patch("avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result):
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)
    subdir = next(tmp_path.iterdir())
    assert subdir.name.startswith("bd_")


@pytest.mark.req("req-sweep-5")
def test_run_raises_on_avl_failure(tmp_path):
    mock_result = _make_mock_result(returncode=1)
    mock_result.stdout = "some output"
    with patch("avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="AVL exited with code 1"):
            run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)


@pytest.mark.req("req-sweep-6")
def test_run_load_command_contains_avl_name(tmp_path):
    captured = {}
    mock_result = _make_mock_result()

    def capture(cmd_text, **kwargs):
        captured["cmd_text"] = cmd_text
        return mock_result

    with patch("avl_aero_tables.avl_sweep.avl_runner.run", side_effect=capture):
        run(BD_AVL, alpha=[5.0], beta=[0.0], out_dir=tmp_path)

    assert captured["cmd_text"].startswith("LOAD bd.avl")


@pytest.mark.req("req-sweep-7")
def test_run_command_contains_alpha(tmp_path):
    captured = {}
    mock_result = _make_mock_result()

    def capture(cmd_text, **kwargs):
        captured["cmd"] = cmd_text
        return mock_result

    with patch("avl_aero_tables.avl_sweep.avl_runner.run", side_effect=capture):
        run(BD_AVL, alpha=[7.5], beta=[0.0], out_dir=tmp_path)

    assert "A A 7.500000" in captured["cmd"]


@pytest.mark.req("req-sweep-8")
def test_run_raises_if_out_dir_not_specified():
    with pytest.raises(TypeError, match="out_dir is required"):
        run(BD_AVL, alpha=[0.0], beta=[0.0])


# ---------------------------------------------------------------------------
# out_format — unit tests (runner + st_fileread both mocked)
# ---------------------------------------------------------------------------


def _fake_results() -> list[StResult]:
    r = StResult(filename="case_0001.st")
    r.data = {"Alpha": 5.0, "Beta": 0.0, "CLtot": 0.58447}
    return [r]


def _run_with_format(out_dir, fmt):
    mock_result = _make_mock_result()
    with patch("avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result):
        with patch(
            "avl_aero_tables.avl_sweep.st_fileread", return_value=_fake_results()
        ):
            run(BD_AVL, alpha=[5.0], beta=[0.0], out_dir=out_dir, out_format=fmt)


@pytest.mark.req("req-sweep-9")
def test_out_format_csv_creates_file(tmp_path):
    _run_with_format(tmp_path, "csv")
    assert any(tmp_path.rglob("results.csv"))


@pytest.mark.req("req-sweep-10")
def test_out_format_json_creates_file(tmp_path):
    _run_with_format(tmp_path, "json")
    assert any(tmp_path.rglob("results.json"))


@pytest.mark.req("req-sweep-11")
def test_out_format_df_writes_no_file(tmp_path):
    _run_with_format(tmp_path, "df")
    assert not any(tmp_path.rglob("results.*"))


@pytest.mark.req("req-sweep-12")
def test_out_format_invalid_raises(tmp_path):
    with pytest.raises(ValueError, match="not recognised"):
        _run_with_format(tmp_path, "xlsx")


@pytest.mark.req("req-sweep-15")
def test_run_writes_sweep_inp(tmp_path):
    mock_result = _make_mock_result()
    with patch("avl_aero_tables.avl_sweep.avl_runner.run", return_value=mock_result):
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path)
    inps = list(tmp_path.rglob(".in/sweep.inp"))
    assert len(inps) == 1
    content = inps[0].read_text()
    assert "LOAD" in content
    assert "CASE" in content


# ---------------------------------------------------------------------------
# Integration test — skipped if AVL binary not installed
# ---------------------------------------------------------------------------


def _avl_installed() -> bool:
    from avl_aero_tables.avl_bin import find_avl

    try:
        find_avl()
        return True
    except FileNotFoundError:
        return False


@pytest.mark.req("req-sweep-13")
@pytest.mark.skipif(not _avl_installed(), reason="AVL binary not installed")
def test_integration_bd_single_point(tmp_path):
    results = run(BD_AVL, alpha=[5.0], beta=[0.0], out_dir=tmp_path)
    assert len(results) >= 1
    r = results[0]
    assert pytest.approx(5.0, abs=0.1) == r.data["Alpha"]
    assert "CLtot" in r.data
    assert "CLa" in r.data


@pytest.mark.req("req-sweep-14")
@pytest.mark.skipif(not _avl_installed(), reason="AVL binary not installed")
def test_perf_bd_full_aero_table(tmp_path):
    alpha = list(range(-5, 16, 5))  # [-5, 0, 5, 10, 15]
    beta = list(range(-5, 6, 5))  # [-5, 0, 5]
    sweeps = {
        "flap": [-10.0, 0.0, 10.0],
        "aileron": [-15.0, 0.0, 15.0],
        "elevator": [-20.0, 0.0, 20.0],
        "rudder": [-20.0, 0.0, 20.0],
    }
    expected = len(alpha) * len(beta) * sum(len(v) for v in sweeps.values())  # 180

    t0 = time.perf_counter()
    results = run(
        BD_AVL,
        alpha=alpha,
        beta=beta,
        ctrl_sweeps=sweeps,
        out_dir=tmp_path,
        out_format="df",
    )
    elapsed = time.perf_counter() - t0

    ms_per_case = elapsed / expected * 1000
    print(
        f"\nbd full sweep: {expected} cases in {elapsed:.1f}s ({ms_per_case:.0f} ms/case)"
    )
    assert len(results) == expected
    assert ms_per_case < 250, f"{ms_per_case:.0f} ms/case exceeds 250 ms/case budget"
