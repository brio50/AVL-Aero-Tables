# aero_fileplot

Generates interactive 3-D surface plots of an `AeroDatabase`.  Three functions, each returning a `dict[str, plotly.Figure]`:

- `plot_totals`: total coefficients vs. $\alpha$/$\beta$ (stability) and $\alpha$/$\delta$ (per control surface)
- `plot_stab_derivs`: stability derivatives $\partial C/\partial(\alpha, \beta, p', q', r')$, one figure per perturbation variable
- `plot_ctrl_derivs`: control derivatives $\partial C/\partial\delta_\text{surface}$, one figure per control surface

```{eval-rst}
.. automodule:: avl_aero_tables.aero_fileplot
   :members:
   :undoc-members: False
   :show-inheritance:
```
