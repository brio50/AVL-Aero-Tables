"""Tests for avl_cli: YAML-driven sweep interface."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from avl_aero_tables.avl_cli import (
    _TIMESTAMP_RE,
    main,
)
from avl_aero_tables.avl_config import ProjectConfig, load_config as _load_config

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
    yml.write_text(
        "input:\n  geometry: x.avl\nsweep:\n  alpha: [0]\n  beta: []\n"
    )
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


def test_load_config_non_numeric_alpha_exits(tmp_path):
    yml = tmp_path / "bad.yml"
    yml.write_text(
        "input:\n  geometry: x.avl\nsweep:\n  alpha: [foo]\n  beta: [0]\n"
    )
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
    assert out_dir.parent.name == "bd"
    assert out_dir.parent.parent.name == "_runs"
    assert out_dir.parent.parent.parent == sub.parent
    assert _TIMESTAMP_RE.match(out_dir.name)


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
        patch("matplotlib.pyplot.show"),
    ):
        result = main(["plot", "geometry", str(yml)])

    assert result == 0
    mock_plot.assert_called_once_with(fake_geom)


# ---------------------------------------------------------------------------
# plot aero — latest-dir discovery
# ---------------------------------------------------------------------------


def test_plot_aero_picks_latest_dir(tmp_path):
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
        patch("avl_aero_tables.aero_fileplot.aero_fileplot"),
        patch("matplotlib.pyplot.show"),
    ):
        result = main(["plot", "aero", str(runs_base)])

    assert result == 0
    assert len(captured) == 1
    assert captured[0] == new_dir / ".raw"


def test_plot_aero_specific_dir(tmp_path):
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
        patch("avl_aero_tables.aero_fileplot.aero_fileplot"),
        patch("matplotlib.pyplot.show"),
    ):
        result = main(["plot", "aero", str(specific_dir)])

    assert result == 0
    assert captured[0] == specific_dir / ".raw"


# ---------------------------------------------------------------------------
# plot aero — no results error
# ---------------------------------------------------------------------------


def test_plot_aero_no_results_exits(tmp_path):
    empty_dir = tmp_path / "_runs" / "bd"
    empty_dir.mkdir(parents=True)

    result = main(["plot", "aero", str(empty_dir)])
    assert result == 1


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
