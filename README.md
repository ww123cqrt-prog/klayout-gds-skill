# KLayout GDS Skill

This skill provides KLayout integration for GDS/OAS layout generation using the embedded Python API (`pya`).

## Documentation

See [SKILL.md](SKILL.md) for detailed usage instructions.

## Quick Start

1. Ensure KLayout is installed
2. Use the provided scripts via `run_klayout_python.py`
3. Generate layouts from interval data or custom polygons

## Scripts

- `run_klayout_python.py` - Launch KLayout Python macros
- `draw_rects_from_intervals.py` - Create layouts from x intervals
- `sample_gds_centerline.py` - Sample centerline occupancy for verification

## Requirements

- KLayout installed (auto-detected from common locations)
- Python 3.x (for script execution)