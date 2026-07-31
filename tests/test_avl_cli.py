"""Tests for avl_cli: YAML-driven sweep interface."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avl_aero_tables.avl_cli import (
    main,
)
from avl_aero_tables.avl_config import ProjectConfig
from avl_aero_tables.avl_config import load_config as _load_config

EXAMPLES = Path(__file__).parent.parent / "examples"
BD_YML = EXAMPLES / "bd" / "bd.yml"

_MINIMAL_YML = textwrap.dedent("""\
    input:
      geometry: {avl_file}
    sweep:
      alpha: {alpha}
      beta: [0]
    """)


def _write_yml(path: Path, avl_file: str = "x.avl", alpha: str = "[0]") -> None:
    path.write_text(_MINIMAL_YML.format(avl_file=avl_file, alpha=alpha))


# ---------------------------------------------------------------------------
# yml loading / pydantic validation
# ---------------------------------------------------------------------------


def test_load_config_bd_roundtrip():
    cfg = _load_config(BD_YML)
    assert cfg.input.geometry == "bd.avl"
    assert cfg.sweep.alpha == [-5, 0, 5, 10, 15]
    assert cfg.sweep.beta == [0]
    assert "elevator" in cfg.sweep.ctrl_sweeps
    assert cfg.output.format == "csv"


def test_load_config_missing_sweep_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text("input:\n  geometry: x.avl\n")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_missing_input_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text("sweep:\n  alpha: [0]\n  beta: [0]\n")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_empty_alpha_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    _write_yml(yml, alpha="[]")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_invalid_format_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: x.avl
        sweep:
          alpha: [0]
          beta: [0]
        output:
          format: xlsx
    """)
    )
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_empty_beta_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    _write_yml(yml, alpha="[0]")
    yml.write_text("input:\n  geometry: x.avl\nsweep:\n  alpha: [0]\n  beta: []\n")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_ctrl_sweeps_empty_list_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: x.avl
        sweep:
          alpha: [0]
          beta: [0]
          ctrl_sweeps:
            elevator: []
    """)
    )
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_sweep_spec_warns_when_ctrl_sweeps_missing_zero(tmp_path):
    from avl_aero_tables.avl_config import SweepSpec

    with pytest.warns(UserWarning, match="no 0.0 deflection"):
        SweepSpec.model_validate(
            {"alpha": [0.0], "beta": [0.0], "ctrl_sweeps": {"elevator": [-10.0, 10.0]}}
        )


def test_sweep_spec_inserts_zero_into_ctrl_sweeps():
    import warnings

    from avl_aero_tables.avl_config import SweepSpec

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        spec = SweepSpec.model_validate(
            {"alpha": [0.0], "beta": [0.0], "ctrl_sweeps": {"elevator": [-10.0, 10.0]}}
        )
    assert 0.0 in spec.ctrl_sweeps["elevator"]
    assert spec.ctrl_sweeps["elevator"] == sorted(spec.ctrl_sweeps["elevator"])


def test_sweep_spec_mode_defaults_to_independent():
    from avl_aero_tables.avl_config import SweepSpec

    spec = SweepSpec.model_validate({"alpha": [0.0], "beta": [0.0]})
    assert spec.mode == "independent"


def test_sweep_spec_mode_accepts_combinatorial():
    from avl_aero_tables.avl_config import SweepSpec

    spec = SweepSpec.model_validate(
        {"alpha": [0.0], "beta": [0.0], "mode": "combinatorial"}
    )
    assert spec.mode == "combinatorial"


def test_load_config_invalid_mode_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: x.avl
        sweep:
          alpha: [0]
          beta: [0]
          mode: sometimes
    """)
    )
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_non_numeric_alpha_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text("input:\n  geometry: x.avl\nsweep:\n  alpha: [foo]\n  beta: [0]\n")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_load_config_invalid_yaml_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text(": bad: yaml: [")
    with pytest.raises(SystemExit):
        _load_config(yml)


def test_project_config_defaults():
    cfg = ProjectConfig.model_validate(
        {
            "input": {"geometry": "x.avl"},
            "sweep": {"alpha": [0], "beta": [0]},
        }
    )
    assert cfg.sweep.ctrl_sweeps == {}
    assert cfg.output.format == "csv"


# ---------------------------------------------------------------------------
# path resolution
# ---------------------------------------------------------------------------


def test_path_resolution_relative_to_yml(tmp_path):
    sub = tmp_path / "aircraft"
    sub.mkdir()
    yml = sub / "plane.yml"
    _write_yml(yml, avl_file="plane.avl")
    cfg = _load_config(yml)
    avl_file = (yml.parent / cfg.input.geometry).resolve()
    assert avl_file == (sub / "plane.avl").resolve()
    assert avl_file != (tmp_path / "plane.avl").resolve()


# ---------------------------------------------------------------------------
# out_dir derivation
# ---------------------------------------------------------------------------


def test_out_dir_pattern(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    _write_yml(yml, avl_file="bd.avl")

    captured: list[Path] = []

    def fake_run(**kwargs: object) -> list[object]:
        captured.append(kwargs["out_dir"])  # type: ignore[arg-type]
        return []

    with patch("avl_aero_tables.avl_sweep.run", side_effect=fake_run):
        main(["sweep", str(yml)])

    assert len(captured) == 1
    out_dir = captured[0]
    assert out_dir.name == "bd"
    assert out_dir.parent.name == "_runs"
    assert out_dir.parent.parent == sub.parent


# ---------------------------------------------------------------------------
# sweep integration (mock avl_sweep.run)
# ---------------------------------------------------------------------------


def test_sweep_passes_correct_args(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: bd.avl
        sweep:
          alpha: [-5, 0, 5]
          beta: [0]
          ctrl_sweeps:
            elevator: [-10, 0, 10]
        output:
          format: json
    """)
    )
    (sub / "bd.avl").touch()

    captured: dict[str, object] = {}

    def fake_run(**kwargs: object) -> list[object]:
        captured.update(kwargs)
        return []

    fake_geom = MagicMock()
    fake_geom.ctrl_names = ["elevator"]

    with (
        patch("avl_aero_tables.avl_fileread.avl_fileread", return_value=fake_geom),
        patch("avl_aero_tables.avl_sweep.run", side_effect=fake_run),
    ):
        result = main(["sweep", str(yml)])

    assert result == 0
    assert captured["avl_file"] == (sub / "bd.avl").resolve()
    assert captured["alpha"] == [-5, 0, 5]
    assert captured["beta"] == [0]
    assert captured["ctrl_sweeps"] == {"elevator": [-10, 0, 10]}
    assert captured["out_format"] == "json"
    assert captured["mode"] == "independent"


def test_sweep_passes_mode_to_run(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: bd.avl
        sweep:
          alpha: [-5, 0, 5]
          beta: [0]
          ctrl_sweeps:
            elevator: [-10, 0, 10]
            rudder: [-10, 0, 10]
          mode: combinatorial
    """)
    )
    (sub / "bd.avl").touch()

    captured: dict[str, object] = {}

    def fake_run(**kwargs: object) -> list[object]:
        captured.update(kwargs)
        return []

    fake_geom = MagicMock()
    fake_geom.ctrl_names = ["elevator", "rudder"]

    with (
        patch("avl_aero_tables.avl_fileread.avl_fileread", return_value=fake_geom),
        patch("avl_aero_tables.avl_sweep.run", side_effect=fake_run),
    ):
        result = main(["sweep", str(yml)])

    assert result == 0
    assert captured["mode"] == "combinatorial"


def test_sweep_bad_ctrl_key_exits(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    yml.write_text(
        textwrap.dedent("""\
        input:
          geometry: bd.avl
        sweep:
          alpha: [0]
          beta: [0]
          ctrl_sweeps:
            florp: [-10, 0, 10]
    """)
    )
    (sub / "bd.avl").touch()

    fake_geom = MagicMock()
    fake_geom.ctrl_names = ["elevator", "aileron"]

    with (
        patch("avl_aero_tables.avl_fileread.avl_fileread", return_value=fake_geom),
        pytest.raises(SystemExit),
    ):
        main(["sweep", str(yml)])


# ---------------------------------------------------------------------------
# plot geometry (mock avl_fileplot + plt.show)
# ---------------------------------------------------------------------------


def test_plot_geometry_calls_fileplot(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    _write_yml(yml, avl_file="bd.avl")

    fake_geom = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.avl_fileread", return_value=fake_geom),
        patch("avl_aero_tables.avl_fileplot.avl_fileplot") as mock_plot,
        patch("webbrowser.open"),
    ):
        result = main(["plot", "geometry", str(yml)])

    assert result == 0
    mock_plot.assert_called_once_with(fake_geom)


# ---------------------------------------------------------------------------
# verify
# ---------------------------------------------------------------------------


def test_verify_ok():
    with patch(
        "avl_aero_tables.avl_cli.verify", return_value=Path("/usr/local/bin/avl")
    ):
        result = main(["verify"])
    assert result == 0


def test_verify_binary_not_found():
    with patch(
        "avl_aero_tables.avl_cli.verify", side_effect=FileNotFoundError("not found")
    ):
        result = main(["verify"])
    assert result == 1


def test_verify_runtime_error():
    with patch(
        "avl_aero_tables.avl_cli.verify", side_effect=RuntimeError("bad binary")
    ):
        result = main(["verify"])
    assert result == 1


# ---------------------------------------------------------------------------
# plot geometry — output file
# ---------------------------------------------------------------------------


def test_plot_geometry_writes_html(tmp_path):
    sub = tmp_path / "bd"
    sub.mkdir()
    yml = sub / "bd.yml"
    _write_yml(yml, avl_file="bd.avl")
    (sub / "bd.avl").touch()

    fake_geom = MagicMock()
    fake_fig = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.avl_fileread", return_value=fake_geom),
        patch("avl_aero_tables.avl_fileplot.avl_fileplot", return_value=fake_fig),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "geometry", str(yml)])

    assert result == 0
    assert fake_fig.write_html.call_count == 1
    written_path = Path(fake_fig.write_html.call_args[0][0])
    assert written_path.name == "bd_geometry.html"
    assert written_path.parent == sub


# ---------------------------------------------------------------------------
# plot totals — latest-dir discovery
# ---------------------------------------------------------------------------


def test_plot_totals_picks_latest_dir(tmp_path):
    runs_base = tmp_path / "_runs" / "bd"
    runs_base.mkdir(parents=True)
    old_dir = runs_base / "2026-01-01-120000"
    new_dir = runs_base / "2026-05-15-093000"
    old_dir.mkdir()
    new_dir.mkdir()

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_totals"),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "totals", str(runs_base)])

    assert result == 0
    assert len(captured) == 1
    assert captured[0] == new_dir / ".raw"


def test_plot_totals_specific_dir(tmp_path):
    runs_base = tmp_path / "_runs" / "bd"
    specific_dir = runs_base / "2026-01-01-120000"
    specific_dir.mkdir(parents=True)

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_totals"),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "totals", str(specific_dir)])

    assert result == 0
    assert captured[0] == specific_dir / ".raw"


# ---------------------------------------------------------------------------
# plot totals — no results error
# ---------------------------------------------------------------------------


def test_plot_totals_no_results_exits(tmp_path):
    empty_dir = tmp_path / "_runs" / "bd"
    empty_dir.mkdir(parents=True)

    result = main(["plot", "totals", str(empty_dir)])
    assert result == 1


def test_plot_totals_nonexistent_dir_exits(tmp_path):
    missing = tmp_path / "does_not_exist"
    result = main(["plot", "totals", str(missing)])
    assert result == 1


def test_plot_totals_prefixed_timestamp_dir(tmp_path):
    """Regression: bd_2026-05-16-215002 style dir passed directly must work."""
    run_dir = tmp_path / "bd_2026-05-16-215002"
    run_dir.mkdir()

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_totals"),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "totals", str(run_dir)])

    assert result == 0
    assert captured[0] == run_dir / ".raw"


def test_plot_totals_raw_dir_fallback(tmp_path):
    """Dir with .raw subdir (non-timestamp name) is recognized as a run dir."""
    run_dir = tmp_path / "my_custom_run"
    (run_dir / ".raw").mkdir(parents=True)

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_totals"),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "totals", str(run_dir)])

    assert result == 0
    assert captured[0] == run_dir / ".raw"


def test_plot_totals_writes_html_files(tmp_path):
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_figs = {
        "stab": MagicMock(),
        "ctrl_lift": MagicMock(),
        "ctrl_side": MagicMock(),
        "ctrl_drag": MagicMock(),
        "ctrl_roll": MagicMock(),
        "ctrl_pitch": MagicMock(),
        "ctrl_yaw": MagicMock(),
    }
    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_totals", return_value=fake_figs),
        patch("webbrowser.open") as mock_browser,
    ):
        result = main(["plot", "totals", str(run_dir)])

    assert result == 0
    for key, fig in fake_figs.items():
        written = Path(fig.write_html.call_args[0][0])
        assert written == run_dir / f"total_{key}.html"
    opened_uri = mock_browser.call_args[0][0]
    assert opened_uri.endswith("index.html")


def test_plot_totals_beta_ref_flag(tmp_path):
    """--beta-ref is forwarded to plot_totals."""
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch(
            "avl_aero_tables.aero_fileplot.plot_totals", return_value={}
        ) as mock_plot,
        patch("webbrowser.open"),
    ):
        main(["plot", "totals", "--beta-ref", "5.0", str(run_dir)])

    _, kwargs = mock_plot.call_args
    assert kwargs.get("beta_ref") == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# plot stab-deriv
# ---------------------------------------------------------------------------


def test_plot_stab_deriv_picks_latest_dir(tmp_path):
    runs_base = tmp_path / "_runs" / "bd"
    old_dir = runs_base / "2026-01-01-120000"
    new_dir = runs_base / "2026-05-15-093000"
    old_dir.mkdir(parents=True)
    new_dir.mkdir()

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_stab_derivs", return_value={}),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "stab-deriv", str(runs_base)])

    assert result == 0
    assert captured[0] == new_dir / ".raw"


def test_plot_stab_deriv_writes_html_files(tmp_path):
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_figs = {name: MagicMock() for name in ["alpha", "beta", "p", "q", "r"]}
    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_stab_derivs", return_value=fake_figs),
        patch("webbrowser.open") as mock_browser,
    ):
        result = main(["plot", "stab-deriv", str(run_dir)])

    assert result == 0
    for key, fig in fake_figs.items():
        written = Path(fig.write_html.call_args[0][0])
        assert written == run_dir / f"deriv_stab_{key}.html"
    assert mock_browser.call_args[0][0].endswith("index.html")


# ---------------------------------------------------------------------------
# plot ctrl-deriv
# ---------------------------------------------------------------------------


def test_plot_ctrl_deriv_picks_latest_dir(tmp_path):
    runs_base = tmp_path / "_runs" / "bd"
    old_dir = runs_base / "2026-01-01-120000"
    new_dir = runs_base / "2026-05-15-093000"
    old_dir.mkdir(parents=True)
    new_dir.mkdir()

    captured: list[Path] = []

    def fake_st_fileread(path: Path) -> list[object]:
        captured.append(path)
        return []

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", side_effect=fake_st_fileread),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_ctrl_derivs", return_value={}),
        patch("webbrowser.open"),
    ):
        result = main(["plot", "ctrl-deriv", str(runs_base)])

    assert result == 0
    assert captured[0] == new_dir / ".raw"


def test_plot_ctrl_deriv_writes_html_files(tmp_path):
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_aero = MagicMock()
    fake_figs = {"flap": MagicMock(), "elevator": MagicMock()}
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch("avl_aero_tables.aero_fileplot.plot_ctrl_derivs", return_value=fake_figs),
        patch("webbrowser.open") as mock_browser,
    ):
        result = main(["plot", "ctrl-deriv", str(run_dir)])

    assert result == 0
    written_names = [
        Path(fig.write_html.call_args[0][0]).name for fig in fake_figs.values()
    ]
    assert written_names == ["deriv_ctrl_flap.html", "deriv_ctrl_elevator.html"]
    assert mock_browser.call_args[0][0].endswith("index.html")


# ---------------------------------------------------------------------------
# plot all
# ---------------------------------------------------------------------------


def test_plot_all_calls_all_three_plotters(tmp_path):
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_aero = MagicMock()
    fake_totals = {"stab": MagicMock(), "ctrl_lift": MagicMock()}
    fake_stab = {"alpha": MagicMock(), "beta": MagicMock()}
    fake_ctrl = {"flap": MagicMock()}

    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch(
            "avl_aero_tables.aero_fileplot.plot_totals", return_value=fake_totals
        ) as mock_totals,
        patch(
            "avl_aero_tables.aero_fileplot.plot_stab_derivs", return_value=fake_stab
        ) as mock_stab,
        patch(
            "avl_aero_tables.aero_fileplot.plot_ctrl_derivs", return_value=fake_ctrl
        ) as mock_ctrl,
        patch("webbrowser.open") as mock_browser,
    ):
        result = main(["plot", "all", str(run_dir)])

    assert result == 0
    mock_totals.assert_called_once()
    mock_stab.assert_called_once()
    mock_ctrl.assert_called_once()
    assert mock_browser.call_args[0][0].endswith("index.html")

    written = {
        Path(fig.write_html.call_args[0][0]).name
        for figs in (fake_totals, fake_stab, fake_ctrl)
        for fig in figs.values()
    }
    assert "total_stab.html" in written
    assert "total_ctrl_lift.html" in written
    assert "deriv_stab_alpha.html" in written
    assert "deriv_stab_beta.html" in written
    assert "deriv_ctrl_flap.html" in written


def test_plot_all_beta_ref_forwarded(tmp_path):
    run_dir = tmp_path / "2026-01-01-120000"
    run_dir.mkdir()

    fake_aero = MagicMock()
    with (
        patch("avl_aero_tables.avl_fileread.st_fileread", return_value=[]),
        patch("avl_aero_tables.aero_filewrite.aero_filewrite", return_value=fake_aero),
        patch(
            "avl_aero_tables.aero_fileplot.plot_totals", return_value={}
        ) as mock_totals,
        patch("avl_aero_tables.aero_fileplot.plot_stab_derivs", return_value={}),
        patch("avl_aero_tables.aero_fileplot.plot_ctrl_derivs", return_value={}),
        patch("webbrowser.open"),
    ):
        main(["plot", "all", "--beta-ref", "3.0", str(run_dir)])

    _, kwargs = mock_totals.call_args
    assert kwargs.get("beta_ref") == pytest.approx(3.0)


def test_write_index_html(tmp_path):
    from avl_aero_tables.avl_cli import _write_index_html

    (tmp_path / "stab.html").touch()
    (tmp_path / "ctrl_CLtot.html").touch()
    index = _write_index_html(tmp_path)
    content = index.read_text()
    assert "stab" in content
    assert "ctrl_CLtot" in content
    assert "index.html" not in content  # index must not list itself


# ---------------------------------------------------------------------------
# All example ymls — parametrized
# ---------------------------------------------------------------------------

_EXAMPLE_YMLS = sorted(EXAMPLES.glob("*/*.yml"))


@pytest.mark.parametrize("yml_path", _EXAMPLE_YMLS, ids=[p.stem for p in _EXAMPLE_YMLS])
def test_example_yml_parses(yml_path: Path):
    cfg = _load_config(yml_path)
    assert cfg.input.geometry.endswith(".avl")
    assert len(cfg.sweep.alpha) >= 1
    assert len(cfg.sweep.beta) >= 1
    assert cfg.output.format in ("csv", "json", "df")


@pytest.mark.parametrize("yml_path", _EXAMPLE_YMLS, ids=[p.stem for p in _EXAMPLE_YMLS])
def test_example_yml_ctrl_sweeps_match_avl(yml_path: Path):
    from avl_aero_tables.avl_fileread import avl_fileread

    cfg = _load_config(yml_path)
    avl_file = yml_path.parent / cfg.input.geometry
    geometry = avl_fileread(avl_file)
    avl_controls = set(geometry.ctrl_names)
    yml_controls = set(cfg.sweep.ctrl_sweeps.keys())
    unknown = yml_controls - avl_controls
    assert not unknown, (
        f"{yml_path.name} ctrl_sweeps references unknown controls: {unknown}"
    )
