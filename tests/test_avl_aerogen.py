"""Tests for avl_aerogen: orchestration of AVL sweep runs."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avl_wrapper.avl_aerogen import _extract_ctrl_names, run
from avl_wrapper.avl_fileread import avl_fileread

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_AVL = EXAMPLES / "bd.avl"


# ---------------------------------------------------------------------------
# _extract_ctrl_names
# ---------------------------------------------------------------------------


def test_extract_ctrl_names_bd():
    geometry = avl_fileread(BD_AVL)
    names = _extract_ctrl_names(geometry)
    assert "flap" in names
    assert "aileron" in names
    assert "elevator" in names
    assert "rudder" in names


def test_extract_ctrl_names_order_stable():
    geometry = avl_fileread(BD_AVL)
    names1 = _extract_ctrl_names(geometry)
    names2 = _extract_ctrl_names(geometry)
    assert names1 == names2


def test_extract_ctrl_names_no_controls():
    geometry = avl_fileread(EXAMPLES / "ellipg.avl")
    names = _extract_ctrl_names(geometry)
    assert names == []


# ---------------------------------------------------------------------------
# run() — unit tests (subprocess mocked)
# ---------------------------------------------------------------------------


def _make_mock_result(returncode: int = 0) -> MagicMock:
    m = MagicMock()
    m.returncode = returncode
    m.stdout = ""
    m.stderr = ""
    return m


def test_run_calls_avl_runner(tmp_path):
    mock_result = _make_mock_result()
    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result) as mock_run:
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path / "out")
    mock_run.assert_called_once()


def test_run_passes_avl_dir_as_cwd(tmp_path):
    mock_result = _make_mock_result()
    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result) as mock_run:
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path / "out")
    _, kwargs = mock_run.call_args
    assert kwargs["cwd"] == BD_AVL.parent


def test_run_creates_out_dir(tmp_path):
    out = tmp_path / "nested" / "out"
    mock_result = _make_mock_result()
    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result):
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=out)
    assert out.is_dir()


def test_run_removes_stale_st_files(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    stale = out / "old_result.st"
    stale.write_text("stale")
    mock_result = _make_mock_result()
    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result):
        run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=out)
    assert not stale.exists()


def test_run_raises_on_avl_failure(tmp_path):
    mock_result = _make_mock_result(returncode=1)
    mock_result.stdout = "some output"
    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result):
        with pytest.raises(RuntimeError, match="AVL exited with code 1"):
            run(BD_AVL, alpha=[0.0], beta=[0.0], out_dir=tmp_path / "out")


def test_run_command_contains_avl_name(tmp_path):
    captured = {}
    mock_result = _make_mock_result()

    def capture(cmd_text, **kwargs):
        captured["cmd"] = cmd_text
        return mock_result

    with patch("avl_wrapper.avl_aerogen.avl_runner.run", side_effect=capture):
        run(BD_AVL, alpha=[5.0], beta=[0.0], out_dir=tmp_path / "out")

    assert "LOAD bd" in captured["cmd"]


def test_run_command_contains_alpha(tmp_path):
    captured = {}
    mock_result = _make_mock_result()

    def capture(cmd_text, **kwargs):
        captured["cmd"] = cmd_text
        return mock_result

    with patch("avl_wrapper.avl_aerogen.avl_runner.run", side_effect=capture):
        run(BD_AVL, alpha=[7.5], beta=[0.0], out_dir=tmp_path / "out")

    assert "A A 7.500000" in captured["cmd"]


def test_run_default_out_dir_is_relative_to_avl(tmp_path):
    mock_result = _make_mock_result()
    avl_copy = tmp_path / "bd.avl"
    avl_copy.write_text(BD_AVL.read_text())

    with patch("avl_wrapper.avl_aerogen.avl_runner.run", return_value=mock_result):
        run(avl_copy, alpha=[0.0], beta=[0.0])

    expected = tmp_path / "out" / "bd"
    assert expected.is_dir()


# ---------------------------------------------------------------------------
# Integration test — skipped if AVL binary not installed
# ---------------------------------------------------------------------------


def _avl_installed() -> bool:
    from avl_wrapper.avl_bin import find_avl
    try:
        find_avl()
        return True
    except FileNotFoundError:
        return False


@pytest.mark.skipif(not _avl_installed(), reason="AVL binary not installed")
def test_integration_bd_single_point(tmp_path):
    results = run(BD_AVL, alpha=[5.0], beta=[0.0], out_dir=tmp_path / "out")
    assert len(results) >= 1
    r = results[0]
    assert pytest.approx(5.0, abs=0.1) == r.data["Alpha"]
    assert "CLtot" in r.data
    assert "CLa" in r.data
