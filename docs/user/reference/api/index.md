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
    participant SF as st_fileread
    participant FS as 📁 out_dir/

    U->>S: avl_file, α, β, δ, .mass
    S->>FR: avl_file
    FR-->>S: AvlGeometry
    S->>RG: make_run_reset()
    RG->>FS: reset.run
    S->>RG: make_run_command() ×2
    RG->>FS: sweep.log
    RG-->>S: cmd_text
    S->>BN: avl_file, reset.run, cmd_text
    BN->>FS: case_NNNN.st
    S->>SF: out_dir/
    SF-->>S: list[StResult]
    S-->>U: list[StResult]
```

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_sweep` | Top-level orchestrator — the `avl_sweep()` entry point | Yes |
| {doc}`avl_fileread` | Parses `.avl` geometry file → `AvlGeometry` | Yes |
| {doc}`avl_rungen` | Builds `reset.run` and the AVL stdin command script | Internal |
| {doc}`avl_bin` | Locates, verifies, and invokes the AVL Fortran binary via subprocess | Indirect |
| {doc}`st_fileread` | Parses `.st` output files → `list[StResult]` | Yes (advanced) |

````

````{div} full-width mermaid-postsweep

```{mermaid}
:caption: Post-sweep API
flowchart TD
    RES(["📊 list[StResult]"])
    GEOM(["📐 AvlGeometry"])

    FP["🖼️ avl_fileplot()"]
    FW["🗄️ aero_filewrite()"]
    AP["📈 aero_fileplot()"]
    CLI["💻 avl-aero-tables CLI"]

    GEOM --> FP -->|"Figure"| FOUT(["🖼️ four-view plot"])
    RES --> FW -->|"AeroDatabase"| AP -->|"list[Figure]"| AOUT(["📈 aero surface plots"])
    CLI -->|"verify / run"| BIN["⚙️ avl_bin"]

    classDef py fill:#dbeafe,stroke:#3b82f6,color:#1e3a5f
    class FP,FW,AP,CLI,BIN py
```

````

| Component | Role | Public? |
|---|---|---|
| {doc}`avl_fileplot` | Four-view geometry plot → `Figure` | Yes |
| {doc}`aero_filewrite` | Exports results to CSV/JSON; pivots `list[StResult]` → `AeroDatabase` | Yes |
| {doc}`aero_fileplot` | 3-D surface plots of `AeroDatabase` → `list[Figure]` | Yes |
| {doc}`avl_cli` | `avl-aero-tables` CLI entry point (`verify`, `run` subcommands) | CLI only |

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
