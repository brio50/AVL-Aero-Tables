"""Tests for avl_rungen: run-case and command file generation."""

from pathlib import Path

import pytest

from avl_aero_tables.avl_rungen import make_run_command, make_run_reset

CTRL_NAMES = ["flap", "aileron", "elevator", "rudder"]


# ---------------------------------------------------------------------------
# make_run_reset
# ---------------------------------------------------------------------------


@pytest.mark.req("req-cmd-1")
def test_reset_run_has_separator():
    text = make_run_reset("bd", CTRL_NAMES)
    assert "---" in text


@pytest.mark.req("req-cmd-2")
def test_reset_run_case_name():
    text = make_run_reset("bd", CTRL_NAMES)
    assert "Run case  1:  Reset bd" in text


@pytest.mark.req("req-cmd-3")
def test_reset_run_alpha_beta_mapping():
    text = make_run_reset("bd", CTRL_NAMES)
    assert " alpha        ->  alpha       =  0.00000" in text
    assert " beta         ->  beta        =  0.00000" in text


@pytest.mark.req("req-cmd-4")
def test_reset_run_control_mappings():
    text = make_run_reset("bd", CTRL_NAMES)
    for ctrl in CTRL_NAMES:
        assert f" {ctrl:<12} ->  {ctrl:<11} =  0.00000" in text


@pytest.mark.req("req-cmd-3")
def test_reset_run_scalar_alpha():
    text = make_run_reset("bd", CTRL_NAMES)
    assert " alpha     =   0.00000     deg" in text


@pytest.mark.req("req-cmd-5")
def test_reset_run_CDo_from_header():
    text = make_run_reset("bd", CTRL_NAMES, CDoref=0.017)
    assert " CDo       =   0.01700" in text


@pytest.mark.req("req-cmd-6")
def test_reset_run_cg_from_header():
    text = make_run_reset("bd", CTRL_NAMES, Xref=3.4, Yref=0.0, Zref=0.5)
    assert " X_cg      =   3.40000" in text
    assert " Z_cg      =   0.50000" in text


@pytest.mark.req("req-cmd-7")
def test_reset_run_units():
    text = make_run_reset("bd", CTRL_NAMES, Lunit="m", Munit="kg", Tunit="s")
    assert "m/s" in text
    assert "kg/s^3" in text
    assert "kg-m^2" in text


@pytest.mark.req("req-cmd-8")
def test_reset_run_no_controls():
    text = make_run_reset("bare", [])
    assert "Run case  1:  Reset bare" in text
    assert "visc CM_u" in text


# ---------------------------------------------------------------------------
# make_run_command
# ---------------------------------------------------------------------------

OUT_DIR = Path("/tmp/out/bd")
AVL_FILE = "bd.avl"
RUN_FILE = "/tmp/avl_x/reset.run"


@pytest.mark.req("req-cmd-9")
def test_command_starts_with_load():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert text.startswith("LOAD bd.avl")


@pytest.mark.req("req-cmd-18")
def test_command_loads_case_file():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert f"CASE {RUN_FILE}" in text


@pytest.mark.req("req-cmd-10")
def test_command_disables_graphics():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "PLOP\nG\n" in text


@pytest.mark.req("req-cmd-11")
def test_command_opens_oper():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "OPER" in text


@pytest.mark.req("req-cmd-12")
def test_command_ends_with_quit():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "Quit" in text


@pytest.mark.req("req-cmd-13")
def test_command_sets_alpha_beta():
    text = make_run_command([5.0], [3.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "A A 5.000000" in text
    assert "B B 3.000000" in text


@pytest.mark.req("req-cmd-14")
def test_command_saves_st_file():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert ".st" in text
    assert str(OUT_DIR) in text


@pytest.mark.req("req-cmd-15")
def test_command_runs_and_resets():
    text = make_run_command([5.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "\ni\n" in text
    assert "\nx\n" in text
    assert "CINI" in text


@pytest.mark.req("req-cmd-16")
def test_command_ctrl_sweep_deflection():
    text = make_run_command(
        [0.0],
        [0.0],
        CTRL_NAMES,
        {"elevator": [-5.0, 0.0, 5.0]},
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
    )
    assert "D3 D3 -5" in text
    assert "D3 D3 0" in text
    assert "D3 D3 5" in text


@pytest.mark.req("req-cmd-13")
def test_command_alpha_beta_appear_in_commands():
    text = make_run_command([5.0], [-3.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE)
    assert "A A 5.000000" in text
    assert "B B -3.000000" in text


@pytest.mark.req("req-cmd-17")
def test_command_multiple_alphas_produce_multiple_runs():
    text = make_run_command(
        [-6.0, 0.0, 6.0], [0.0], CTRL_NAMES, {}, OUT_DIR, AVL_FILE, RUN_FILE
    )
    assert text.count("A A") == 3  # one run per alpha when no ctrl_sweeps


# ---------------------------------------------------------------------------
# mode="independent" vs mode="combinatorial"
# ---------------------------------------------------------------------------

CTRL_SWEEPS_2SURF = {
    "elevator": [-5.0, 0.0, 5.0],
    "rudder": [-10.0, 0.0, 10.0],
}


@pytest.mark.req("req-cmd-21")
def test_command_mode_defaults_to_independent():
    default_text = make_run_command(
        [0.0], [0.0], CTRL_NAMES, CTRL_SWEEPS_2SURF, OUT_DIR, AVL_FILE, RUN_FILE
    )
    explicit_text = make_run_command(
        [0.0],
        [0.0],
        CTRL_NAMES,
        CTRL_SWEEPS_2SURF,
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
        mode="independent",
    )
    assert default_text == explicit_text


@pytest.mark.req("req-cmd-22")
def test_command_independent_sweeps_one_surface_at_a_time():
    text = make_run_command(
        [0.0],
        [0.0],
        CTRL_NAMES,
        CTRL_SWEEPS_2SURF,
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
        mode="independent",
    )
    # 3 elevator points + 3 rudder points = 6 cases, one Di line per case
    assert text.count("A A") == 6
    assert text.count("D3 D3") == 3  # elevator (index 3)
    assert text.count("D4 D4") == 3  # rudder (index 4)
    # no case sets both D3 and D4 simultaneously
    # text.split("OPER") yields a leading header block and a trailing block
    # after the last case's reopening OPER (just "Quit"); both are excluded.
    for block in text.split("OPER")[1:-1]:
        case_lines = block.splitlines()
        assert not (
            any(line.startswith("D3 D3") for line in case_lines)
            and any(line.startswith("D4 D4") for line in case_lines)
        )


@pytest.mark.req("req-cmd-23")
def test_command_combinatorial_cross_product_case_count():
    text = make_run_command(
        [0.0, 5.0],
        [0.0],
        CTRL_NAMES,
        CTRL_SWEEPS_2SURF,
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
        mode="combinatorial",
    )
    # 2 alpha × 1 beta × (3 elevator × 3 rudder) = 18 cases
    assert text.count("A A") == 18
    assert text.count("D3 D3") == 18
    assert text.count("D4 D4") == 18


@pytest.mark.req("req-cmd-24")
def test_command_combinatorial_deflects_both_surfaces_per_case():
    text = make_run_command(
        [0.0],
        [0.0],
        CTRL_NAMES,
        CTRL_SWEEPS_2SURF,
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
        mode="combinatorial",
    )
    # every case block between successive OPER commands sets both D3 and D4
    # text.split("OPER") yields a leading header block and a trailing block
    # after the last case's reopening OPER (just "Quit"); both are excluded.
    for block in text.split("OPER")[1:-1]:
        case_lines = block.splitlines()
        assert any(line.startswith("D3 D3") for line in case_lines)
        assert any(line.startswith("D4 D4") for line in case_lines)


@pytest.mark.req("req-cmd-25")
def test_command_combinatorial_includes_all_neutral_case():
    text = make_run_command(
        [0.0],
        [0.0],
        CTRL_NAMES,
        CTRL_SWEEPS_2SURF,
        OUT_DIR,
        AVL_FILE,
        RUN_FILE,
        mode="combinatorial",
    )
    assert "D3 D3 0" in text
    assert "D4 D4 0" in text


@pytest.mark.req("req-cmd-26")
def test_command_invalid_mode_raises():
    with pytest.raises(ValueError, match="not recognised"):
        make_run_command(
            [0.0],
            [0.0],
            CTRL_NAMES,
            {},
            OUT_DIR,
            AVL_FILE,
            RUN_FILE,
            mode="both",  # type: ignore[arg-type]
        )
