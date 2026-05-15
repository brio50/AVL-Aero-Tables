"""Tests for avl_bin.py and cli.py: binary discovery, verification, and CLI."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avl_aero_tables.avl_bin import find_avl, run, verify
from avl_aero_tables.avl_cli import _build_parser, main

# ---------------------------------------------------------------------------
# find_avl
# ---------------------------------------------------------------------------


@pytest.mark.req("req-bin-1")
def test_find_avl_finds_local_binary():
    fake_bin = Path.home() / "bin" / "avl"
    if fake_bin.exists():
        result = find_avl()
        assert result == fake_bin


@pytest.mark.req("req-bin-2")
def test_find_avl_raises_when_missing():
    with (
        patch("avl_aero_tables.avl_bin.Path.home", return_value=Path("/nonexistent")),
        patch("avl_aero_tables.avl_bin.shutil.which", return_value=None),
    ):
        with pytest.raises(FileNotFoundError, match="AVL binary not found"):
            find_avl()


@pytest.mark.req("req-bin-3")
def test_find_avl_falls_back_to_path():
    fake_avl = Path("/usr/local/bin/avl")
    with (
        patch("avl_aero_tables.avl_bin.Path.home", return_value=Path("/nonexistent")),
        patch("avl_aero_tables.avl_bin.shutil.which", return_value=str(fake_avl)),
    ):
        result = find_avl()
        assert result == fake_avl


# ---------------------------------------------------------------------------
# verify  (integration — skipped if binary absent)
# ---------------------------------------------------------------------------


def _avl_installed() -> bool:
    try:
        find_avl()
        return True
    except FileNotFoundError:
        return False


@pytest.mark.req("req-bin-4")
@pytest.mark.skipif(not _avl_installed(), reason="AVL binary not installed")
def test_verify_returns_path():
    path = verify()
    assert path.is_file()


@pytest.mark.req("req-bin-5")
@pytest.mark.skipif(not _avl_installed(), reason="AVL binary not installed")
def test_verify_raises_on_bad_binary(tmp_path):
    fake = tmp_path / "avl"
    fake.write_text("#!/bin/sh\nexit 1\n")
    fake.chmod(0o755)
    with pytest.raises(RuntimeError, match="exited with code"):
        verify(fake)


# ---------------------------------------------------------------------------
# run (unit — mock subprocess)
# ---------------------------------------------------------------------------


@pytest.mark.req("req-bin-6")
def test_run_calls_binary_with_stdin():
    mock_result = MagicMock()
    mock_result.returncode = 0

    with (
        patch("avl_aero_tables.avl_bin.find_avl", return_value=Path("/bin/avl")),
        patch(
            "avl_aero_tables.avl_bin.subprocess.run", return_value=mock_result
        ) as mock_run,
    ):
        run("quit\n", avl_file="bd.avl", run_file="/tmp/avl_x/reset.run")
        mock_run.assert_called_once()
        call_args, call_kwargs = mock_run.call_args
        assert call_kwargs["input"] == "quit\n"
        assert call_args[0] == ["/bin/avl", "bd.avl", "/tmp/avl_x/reset.run"]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@pytest.mark.req("req-bin-7")
def test_cli_verify_subcommand_success():
    with (
        patch("avl_aero_tables.avl_cli.verify", return_value=Path("/bin/avl")),
    ):
        code = main(["verify"])
        assert code == 0


@pytest.mark.req("req-bin-7")
def test_cli_verify_subcommand_failure():
    with (
        patch(
            "avl_aero_tables.avl_cli.verify",
            side_effect=FileNotFoundError("AVL binary not found"),
        ),
    ):
        code = main(["verify"])
        assert code == 1


@pytest.mark.req("req-bin-8")
def test_cli_run_subcommand(tmp_path):
    cmd_file = tmp_path / "command.txt"
    cmd_file.write_text("quit\n")

    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = ""
    mock_result.stderr = ""

    with patch("avl_aero_tables.avl_cli.run_file", return_value=mock_result):
        code = main(["run", str(cmd_file)])
        assert code == 0


@pytest.mark.req("req-bin-9")
def test_cli_no_args_shows_help():
    parser = _build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])
