---
name: klayout-gds
description: Use KLayout's embedded Python API (`pya`) to draw, inspect, verify, and export GDS/OAS layouts. Use this skill whenever Codex needs to generate GDS from geometry data, draw photonic/electronic layout rectangles or polygons, run KLayout Python macros, batch-export layouts, convert interval/profile data into layout geometry, or round-trip sample a GDS layout for comparison against numerical profiles such as `n_profile.txt`.
---

# KLayout GDS

## Overview

Use this skill to run KLayout as the geometry engine for layout generation. Ordinary Python may prepare data, but any code that imports `pya` must be executed by KLayout itself.

## Core Rule

Do not run KLayout API scripts with `python3 script.py`. System Python often cannot import `pya`. Run `.py` macros through KLayout:

From the skill directory:

```bash
python scripts/run_klayout_python.py \
  scripts/draw_rects_from_intervals.py \
  --var intervals=/path/to/intervals.csv \
  --var out=/path/to/layout.gds \
  --var width_um=2.5
```

`run_klayout_python.py` detects `KLAYOUT_BIN`, `klayout` on `PATH`, and common macOS app locations such as `/Applications/KLayout.app/Contents/MacOS/klayout`. On Windows, it checks `%APPDATA%\KLayout\klayout_app.exe` and standard `Program Files` locations.

## Workflow

1. Determine the input geometry.
   - For interval/profile tasks, create a text file whose first two numeric columns are `x_start` and `x_stop`.
   - For `.mat`, HDF5, NumPy, or SciPy-heavy inputs, use ordinary Python to convert data to a simple CSV/TSV first. Keep KLayout focused on geometry creation and stream export.
   - For custom polygons, write or adapt a KLayout `.py` script and launch it with `run_klayout_python.py`.
2. Set explicit units.
   - KLayout database coordinates are integer dbu values. Use `dbu_um=0.001` for a 1 nm database unit unless the project requires another value.
   - State whether interval coordinates are already in micrometers. If not, pass `x_scale`; for nm-to-um use `x_scale=0.001`.
3. Generate the layout with KLayout embedded Python.
   - Use `draw_rects_from_intervals.py` for ridge/grating-like layouts.
   - Pass `layer`, `datatype`, `cell`, `width_um`, `y_center_um`, and `merge` explicitly when they matter.
4. Verify the result.
   - Confirm the output file exists and is recognized as a GDS/OAS stream.
   - For profile comparisons, use `sample_gds_centerline.py` to re-read the layout and sample occupancy on the same x grid as the numerical profile.
   - Compare sampled occupancy/profile vectors, not rectangle counts, because touching or overlapping intervals may merge.

## Built-In Scripts

### `scripts/run_klayout_python.py`

Launch any KLayout Python macro through the embedded interpreter:

```bash
python3 C:/Users/11/.agents/skills/klayout-gds-skill/scripts/run_klayout_python.py \
  /path/to/macro.py \
  --var name=value \
  --var another=value
```

Use `--klayout /path/to/klayout` to override auto-detection. Use `--dry-run` to print the command without executing it.

### `scripts/draw_rects_from_intervals.py`

Create a GDS/OAS layout from x intervals. The input file may be comma-, tab-, semicolon-, or whitespace-separated. Blank lines and `#` comments are ignored. By default, the first two numeric columns are interpreted as interval start and stop.

Important variables passed with `--var`:

- `intervals`: required path to the interval text file.
- `out`: required output `.gds` or `.oas` path.
- `width_um`: rectangle width in y, default `2.5`.
- `y_center_um`: rectangle center in y, default `0`.
- `layer` and `datatype`: default `1` and `0`.
- `dbu_um`: database unit in micrometers, default `0.001`.
- `x_scale`: multiplier applied to input x values before drawing, default `1`.
- `x_offset_um`: offset added after scaling, default `0`.
- `merge`: merge touching or overlapping rectangles before export, default `true`.

Example:

```bash
python3 C:/Users/11/.agents/skills/klayout-gds-skill/scripts/run_klayout_python.py \
  C:/Users/11/.agents/skills/klayout-gds-skill/scripts/draw_rects_from_intervals.py \
  --var intervals=/tmp/ridge_intervals.csv \
  --var out=/tmp/ridges.gds \
  --var width_um=2.5 \
  --var layer=1 \
  --var datatype=0
```

### `scripts/sample_gds_centerline.py`

Re-read a GDS/OAS file and sample centerline occupancy for round-trip checks:

```bash
python3 C:/Users/11/.agents/skills/klayout-gds-skill/scripts/run_klayout_python.py \
  C:/Users/11/.agents/skills/klayout-gds-skill/scripts/sample_gds_centerline.py \
  --var gds=/tmp/ridges.gds \
  --var out=/tmp/ridges_profile.csv \
  --var x_start_um=0 \
  --var x_stop_um=10 \
  --var dx_um=0.01 \
  --var y_um=0 \
  --var layer=1 \
  --var datatype=0 \
  --var right_closed=false
```

The output CSV contains `x_um,occupancy`. Use the same sample centers as the numerical profile being checked. For raster/profile comparisons, keep `right_closed=false` so polygon intervals behave as half-open `[left, right)` spans and right-edge samples are not double-counted.

## KLayout Notes

Read `references/klayout-python-patterns.md` when writing custom KLayout Python scripts or debugging macro invocation.
