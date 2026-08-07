# API

`avl_sweep` is the top-level orchestrator. All other components are either called internally by it or used directly by the user afterward.

````{div} full-width mermaid-sweep

```{mermaid}
:caption: Sweep data flow
sequenceDiagram
    actor U as User
    participant S as avl_sweep
    participant FR as avl_fileread
    participant RG as avl_rungen
    participant BN as avl_bin
    participant FS as 📁 out_dir/

    U->>S: avl_file, α, β, δ
    S->>FR: avl_file
    FR-->>S: AvlGeometry
    S->>RG: make_run_reset()
    RG-->>S: content
    S->>FS: .in/reset.run
    S->>RG: make_run_command() ×2
    RG-->>S: cmd_text
    S->>FS: .in/sweep.inp
    S->>BN: cmd_text
    BN->>FS: .raw/case_NNNN.st
    S->>FR: st_fileread(.raw/)
    FR-->>S: list[StResult]
    S->>FS: results_total.csv / .json
    S->>FS: results_deriv_stab.csv / .json
    S->>FS: results_deriv_ctrl.csv / .json
    S-->>U: list[StResult]
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_sweep` | Top-level orchestrator, the `avl_sweep()` entry point | Yes |
| {doc}`avl_fileread` | Parses AVL file formats: `.avl` geometry to `AvlGeometry`; `.st` output to `list[StResult]` | Yes |
| {doc}`avl_rungen` | Builds `.in/reset.run` and `.in/sweep.inp` (the AVL stdin script) | Internal |
| {doc}`avl_bin` | Locates, verifies, and invokes the AVL Fortran binary via subprocess | Indirect |

`out_format` also accepts `"mat"`/`"h5"` (writing `results_total.mat`/`results_total.h5` alongside — or instead of — the `.csv`/`.json` shown above); the `convert` CLI subcommand adds those formats to an *existing* run directory by re-parsing `.raw/` and is not part of this automatic sweep-time write path. See [`.mat` / `.h5` Export](../../concepts.md#mat-h5-export).

````

````{div} full-width mermaid-postsweep

```{mermaid}
:caption: Geometry plot
sequenceDiagram
    actor U as User
    participant FR as avl_fileread
    participant FP as avl_fileplot
    participant FS as 📁 out/

    U->>FR: avl_file
    FR-->>U: AvlGeometry
    U->>FP: AvlGeometry
    FP-->>U: plotly.Figure
    U->>FS: fig.write_html() → .html
```

```{mermaid}
:caption: Aero database + plots
sequenceDiagram
    actor U as User
    participant FW as aero_filewrite
    participant AP as aero_fileplot
    participant FS as 📁 out/

    U->>FW: list[StResult]
    FW-->>U: AeroDatabase
    U->>AP: AeroDatabase
    AP-->>U: dict[str, plotly.Figure]
    U->>FS: fig.write_html() → .html (per key)
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_fileplot` | Interactive four-view geometry plot, returns `plotly.Figure` written to `.html` | Yes |
| {doc}`aero_filewrite` | Exports results to CSV/JSON/`.mat`/`.h5`; pivots `list[StResult]` to `AeroDatabase` | Yes |
| {doc}`aero_fileplot` | Interactive 3-D surface plots, returns `dict[str, plotly.Figure]`, one `.html` per key | Yes |

````

````{div} full-width mermaid-cli

```{mermaid}
:caption: CLI
sequenceDiagram
    actor U as User
    participant CLI as avl_cli
    participant CFG as avl_config
    participant BN as avl_bin
    participant S as avl_sweep
    participant FR as avl_fileread
    participant FP as avl_fileplot / aero_filewrite / aero_fileplot

    U->>CLI: avl-aero-tables <cmd> [args]
    alt verify
        CLI->>BN: verify()
        BN-->>CLI: binary path
    else sweep <yml>
        CLI->>CFG: load_config(yml)
        CFG-->>CLI: ProjectConfig
        CLI->>S: run(avl_file, α, β, δ, out_dir)
        S-->>CLI: list[StResult]
    else plot geometry <yml>
        CLI->>CFG: load_config(yml)
        CFG-->>CLI: ProjectConfig
        CLI->>FR: avl_fileread(avl_file)
        FR-->>CLI: AvlGeometry
        CLI->>FP: avl_fileplot(AvlGeometry)
        FP-->>CLI: Figure
    else plot totals / stab-deriv / ctrl-deriv <runs_dir>
        CLI->>FR: st_fileread(.raw/)
        FR-->>CLI: list[StResult]
        CLI->>FP: aero_filewrite(results)
        FP-->>CLI: AeroDatabase
        CLI->>FP: plot_totals / plot_stab_derivs / plot_ctrl_derivs(db)
        FP-->>CLI: dict[str, Figure]
    end
    CLI-->>U: output / status
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_cli` | `avl-aero-tables` CLI entry point: argument parsing and command dispatch | CLI only |
| {doc}`avl_config` | YAML project-file schema (`ProjectConfig`) and `load_config()` | CLI only |

````

```{toctree}
:maxdepth: 1
:hidden:

avl_sweep
avl_fileread
avl_rungen
avl_bin
aero_filewrite
avl_fileplot
aero_fileplot
avl_cli
avl_config
```
