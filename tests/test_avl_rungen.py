"""Tests for avl_rungen: run-case and command file generation."""

from pathlib import Path

from avl_wrapper.avl_rungen import make_command, make_reset_run

CTRL_NAMES = ["flap", "aileron", "elevator", "rudder"]


# ---------------------------------------------------------------------------
# make_reset_run
# ---------------------------------------------------------------------------


def test_reset_run_has_separator():
    text = make_reset_run("bd", CTRL_NAMES)
    assert "---" in text


def test_reset_run_case_name():
    text = make_reset_run("bd", CTRL_NAMES)
    assert "Run case  1:  Reset bd" in text


def test_reset_run_alpha_beta_mapping():
    text = make_reset_run("bd", CTRL_NAMES)
    assert " alpha        ->  alpha       =  0.00000" in text
    assert " beta         ->  beta        =  0.00000" in text


def test_reset_run_control_mappings():
    text = make_reset_run("bd", CTRL_NAMES)
    for ctrl in CTRL_NAMES:
        assert f" {ctrl:<12} ->  {ctrl:<11} =  0.00000" in text


def test_reset_run_scalar_alpha():
    text = make_reset_run("bd", CTRL_NAMES)
    assert " alpha     =   0.00000     deg" in text


def test_reset_run_CDo_from_header():
    text = make_reset_run("bd", CTRL_NAMES, CDoref=0.017)
    assert " CDo       =   0.01700" in text


def test_reset_run_cg_from_header():
    text = make_reset_run("bd", CTRL_NAMES, Xref=3.4, Yref=0.0, Zref=0.5)
    assert " X_cg      =   3.40000" in text
    assert " Z_cg      =   0.50000" in text


def test_reset_run_units():
    text = make_reset_run("bd", CTRL_NAMES, Lunit="m", Munit="kg", Tunit="s")
    assert "m/s" in text
    assert "kg/s^3" in text
    assert "kg-m^2" in text


def test_reset_run_no_controls():
    text = make_reset_run("bare", [])
    assert "Run case  1:  Reset bare" in text
    assert "visc CM_u" in text


# ---------------------------------------------------------------------------
# make_command
# ---------------------------------------------------------------------------

OUT_DIR = Path("/tmp/out/bd")


def test_command_starts_with_load():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert text.startswith("LOAD bd")


def test_command_disables_graphics():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert "PLOP\nG\n" in text


def test_command_opens_oper():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert "OPER" in text


def test_command_ends_with_quit():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert "Quit" in text


def test_command_sets_alpha_beta():
    text = make_command("bd", [5.0], [3.0], CTRL_NAMES, {}, OUT_DIR)
    assert "A A 5.000000" in text
    assert "B B 3.000000" in text


def test_command_saves_st_file():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert ".st" in text
    assert str(OUT_DIR) in text


def test_command_runs_and_resets():
    text = make_command("bd", [5.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert "\ni\n" in text
    assert "\nx\n" in text
    assert "CINI" in text


def test_command_ctrl_sweep_deflection():
    text = make_command(
        "bd", [0.0], [0.0], CTRL_NAMES, {"elevator": [-5.0, 0.0, 5.0]}, OUT_DIR
    )
    assert "D3 D3 -5" in text
    assert "D3 D3 0" in text
    assert "D3 D3 5" in text


def test_command_alpha_beta_appear_in_commands():
    text = make_command("bd", [5.0], [-3.0], CTRL_NAMES, {}, OUT_DIR)
    assert "A A 5.000000" in text
    assert "B B -3.000000" in text


def test_command_multiple_alphas_produce_multiple_runs():
    text = make_command("bd", [-6.0, 0.0, 6.0], [0.0], CTRL_NAMES, {}, OUT_DIR)
    assert text.count("A A") == 3  # one run per alpha when no ctrl_sweeps
