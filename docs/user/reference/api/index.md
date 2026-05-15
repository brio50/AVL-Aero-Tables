# API

`avl_sweep` is the top-level orchestrator. All other components are either called internally by it or used directly by the user afterward.

````{div} full-width

```{mermaid}
flowchart TD
    User(["User"])

    subgraph sweep ["avl_sweep.run"]
        direction TB
        FR["avl_fileread() → AvlGeometry"]
        RR["make_run_reset() → reset.run"]
        RC["make_run_command() → cmd_text"]
        BN["avl_bin.run() → .st files"]
        MV["stage /tmp → out_dir"]
        SR["st_fileread() → list[StResult]"]
        FW["results_to_dataframe() → results.csv/.json"]

        FR --> RR --> RC --> BN --> MV --> SR
        SR -.->|"out_format ≠ 'df'"| FW
    end

    User -->|"avl_file, α, β, δ, I, ..."| sweep
    sweep -->|"list[StResult]"| User

    User -->|"list[StResult]"| FW2["aero_filewrite() → AeroDatabase"]
    FW2 -->|"AeroDatabase"| AP["aero_fileplot() → list[Figure]"]
    User -->|"AvlGeometry"| FP["avl_fileplot() → Figure"]
    User -->|"verify / run"| CLI["avl-aero-tables CLI → avl_bin"]
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_sweep` | Top-level orchestrator — the `avl_sweep()` entry point | Yes |
| {doc}`avl_fileread` | Parses `.avl` geometry file → `AvlGeometry` | Yes |
| {doc}`avl_rungen` | Builds `reset.run` and the AVL stdin command script | Internal |
| {doc}`avl_bin` | Locates, verifies, and invokes the AVL Fortran binary via subprocess | Indirect |
| {doc}`st_fileread` | Parses `.st` output files → `list[StResult]` | Yes (advanced) |
| {doc}`aero_filewrite` | Exports results to CSV/JSON; pivots `list[StResult]` → `AeroDatabase` | Yes |
| {doc}`avl_fileplot` | Four-view geometry plot → `Figure` | Yes |
| {doc}`aero_fileplot` | 3-D surface plots of `AeroDatabase` → `list[Figure]` | Yes |
| {doc}`avl_cli` | `avl-aero-tables` CLI entry point (`verify`, `run` subcommands) | CLI only |
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
