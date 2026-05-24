# aero_fileplot

Generates interactive 3-D surface plots of an `AeroDatabase`.  Three functions, each returning a `dict[str, plotly.Figure]`:

- `plot_totals` — total coefficients vs. α/β (stability) and α/δ (per control surface)
- `plot_stab_derivs` — stability derivatives ∂C/∂(α, β, p′, q′, r′), one figure per perturbation variable
- `plot_ctrl_derivs` — control derivatives ∂C/∂δ_surface, one figure per control surface

```{eval-rst}
.. automodule:: avl_aero_tables.aero_fileplot
   :members:
   :undoc-members: False
   :show-inheritance:
```
