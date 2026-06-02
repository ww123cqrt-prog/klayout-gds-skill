# KLayout Python Patterns

## Embedded Python

KLayout's Python API lives in its embedded interpreter as `pya`. A normal system Python environment often does not have `pya`, so run layout macros with KLayout:

```bash
klayout -b -rd key=value -r macro.py
```

KLayout selects the macro interpreter from the file suffix. Use a real `.py` file, not a suffix-less process substitution.

## Passing Parameters

Use `-rd name=value` for script parameters. In Python macros, these appear as globals:

```python
out_path = globals().get("out")
width_um = float(globals().get("width_um", 2.5))
```

Use short, identifier-like names for `-rd` variables. Avoid spaces in variable names.

## Units

Set the layout database unit explicitly:

```python
layout = pya.Layout()
layout.dbu = 0.001  # micrometers per dbu, i.e. 1 nm
```

Convert user geometry in micrometers to integer database coordinates:

```python
def to_dbu(value_um, dbu_um):
    return int(round(value_um / dbu_um))
```

When comparing layout against numerical profiles, compare sampled values on the same x grid instead of comparing polygon counts. KLayout may merge touching shapes, and database-unit rounding can move boundaries by roughly half a dbu.

## Rectangles and Layers

Create a cell, resolve a layer/datatype pair, and insert boxes:

```python
layout = pya.Layout()
layout.dbu = 0.001
top = layout.create_cell("TOP")
layer_index = layout.layer(1, 0)
top.shapes(layer_index).insert(pya.Box(0, -1250, 1000, 1250))
layout.write("/tmp/out.gds")
```

For many rectangles that should become a continuous mask, insert them into a `pya.Region`, call `merge()`, then insert merged polygons into the target layer.

## Data Preparation

Keep parsing-heavy work outside KLayout when possible. For `.mat`, HDF5, pandas, NumPy, SciPy, or project-specific optimization data, first write a simple CSV/TSV interval file with ordinary Python. Then let KLayout's embedded Python consume that stable geometry format and write the final GDS/OAS stream.
