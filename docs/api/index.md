# API Reference

The diagram below traces a full analysis run — from calling `avl_sweep()` through to plotting the aero database. `avl_sweep` is the orchestrator; all other components are either called by it internally or by the user directly afterward.

````{div} full-width
```{mermaid}
sequenceDiagram
    actor User
    participant AE as avl_sweep
    participant FR as avl_fileread
    participant RG as avl_rungen
    participant BN as avl_bin
    participant SR as st_fileread
    participant FW as aero_filewrite
    participant FP as avl_fileplot
    participant AP as aero_fileplot
    participant CL as avl_cli

    User->>AE: avl_sweep(avl_file, alpha, beta, ctrl_sweeps)
    AE->>FR: avl_fileread(avl_file)
    FR-->>AE: AvlGeometry
    AE->>RG: make_command(avl_name, alpha, beta, ctrl_names, ctrl_sweeps, staging)
    RG-->>AE: command string
    AE->>BN: run(cmd_text, cwd=avl_dir)
    BN-->>AE: CompletedProcess
    Note over AE: move .st files from /tmp staging → out_dir
    AE->>SR: st_fileread(out_dir)
    SR-->>AE: list[StResult]
    opt out_format != "df"
        AE->>FW: results_to_dataframe(results)
        FW-->>AE: DataFrame → results.csv / .json
    end
    AE-->>User: list[StResult]

    User->>CL: avl-wrapper verify / run
    CL->>BN: verify() / run_file()
    BN-->>CL: result
    CL-->>User: exit code

    User->>FW: aero_filewrite(results)
    FW-->>User: AeroDatabase

    User->>FP: avl_fileplot(geom)
    FP-->>User: Figure

    User->>AP: aero_fileplot(aero, beta_ref)
    AP-->>User: list[Figure]
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_sweep` | Top-level orchestrator — the `avl_sweep()` entry point | Yes |
| {doc}`avl_fileread` | Parses `.avl` geometry file → `AvlGeometry` | Yes |
| {doc}`avl_rungen` | Builds the AVL stdin command script | Internal |
| {doc}`avl_bin` | Locates, verifies, and invokes the AVL Fortran binary via subprocess | Indirect |
| {doc}`st_fileread` | Parses `.st` output files → `list[StResult]` | Yes (advanced) |
| {doc}`aero_filewrite` | Exports results to CSV/JSON; pivots `list[StResult]` → `AeroDatabase` | Yes |
| {doc}`avl_fileplot` | Four-view geometry plot → `Figure` | Yes |
| {doc}`aero_fileplot` | 3-D surface plots of `AeroDatabase` → `list[Figure]` | Yes |
| {doc}`avl_cli` | `avl-wrapper` CLI entry point (`verify`, `run` subcommands) | CLI only |

````

```{toctree}
:maxdepth: 1
:hidden:

avl_sweep
avl_fileread
avl_rungen
avl_bin
st_fileread
aero_filewrite
avl_fileplot
aero_fileplot
avl_cli
```
