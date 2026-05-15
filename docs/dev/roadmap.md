# Roadmap

Ideas and design concepts for future development of `avl-aero-tables`.

```{note}
Nothing on this page is implemented yet. These are proposals and sketches only.
```

## UI Concept

The sketch below outlines a potential graphical interface — a browser-based or desktop UI for setting up geometry, configuring sweeps, and exploring aero database results without writing Python directly.

```{raw} html
<object data="../_static/AVL.pdf" type="application/pdf" width="100%" height="700px">
  <a href="../_static/AVL.pdf">Download UI concept sketch (PDF)</a>
</object>
```

## Planned features

- **scipy interpolation**: add `scipy.interpolate.RegularGridInterpolator` support to `AeroDatabase` so users can query coefficients at arbitrary `(alpha, beta, defl)` points between breakpoints. The numpy arrays in `StabTable` and `CtrlTable` are already shaped correctly for `RegularGridInterpolator`. Expose as an `interpolate(coef, alpha, beta, defl=0.0)` method or standalone helper.

- **Versioned docs**: `sphinx-multiversion` to build a separate HTML tree per git tag with a version-switcher dropdown on the docs site.

- **Multi-format export**: add export targets to `aero_filewrite` beyond the current pandas/CSV path.
  - `.mat` via `scipy.io.savemat` — writes `AeroDatabase` as a MATLAB struct for direct use in Simulink lookup tables. `StabTable` and `CtrlTable` numpy arrays map cleanly to struct fields.
  - `.h5` via `h5py` — HDF5 as the Python-native equivalent. Preserves hierarchy (`/stab/CLtot`, `/ctrl/aileron/CLtot`, `/breakpoints/alpha`, etc.) and is readable from MATLAB via `h5read`. Suitable for post-processing in Python without a MATLAB install.
  - Expose as `aero_filewrite(results, path, fmt="mat"|"h5")` or standalone `aero_to_mat` / `aero_to_hdf5` helpers.
