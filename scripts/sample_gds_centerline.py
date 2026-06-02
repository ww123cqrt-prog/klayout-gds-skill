"""KLayout embedded-Python macro: sample GDS/OAS occupancy along a horizontal line."""

from __future__ import annotations

import csv
import math
import os
import sys

import pya


def rd(name: str, default: object | None = None) -> object | None:
    return globals().get(name, default)


def require_rd(name: str) -> str:
    value = rd(name)
    if value is None or str(value) == "":
        raise ValueError(f"Missing required -rd variable: {name}")
    return str(value)


def as_float(name: str, default: float | None = None) -> float:
    value = rd(name, default)
    if value is None or str(value) == "":
        raise ValueError(f"Missing required numeric -rd variable: {name}")
    try:
        return float(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a number, got {value!r}") from exc


def as_int(name: str, default: int) -> int:
    value = rd(name, default)
    try:
        return int(value)
    except Exception as exc:
        raise ValueError(f"{name} must be an integer, got {value!r}") from exc


def as_bool(name: str, default: bool) -> bool:
    value = rd(name, "true" if default else "false")
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def to_dbu(value_um: float, dbu_um: float) -> int:
    return int(round(value_um / dbu_um))


def from_dbu(value_dbu: int, dbu_um: float) -> float:
    return value_dbu * dbu_um


def merged_layer_region(layout: pya.Layout, cell: pya.Cell, layer: int, datatype: int) -> pya.Region:
    layer_index = layout.layer(layer, datatype)
    region = pya.Region(cell.begin_shapes_rec(layer_index))
    region.merge()
    return region


def intervals_from_band(
    region: pya.Region,
    x_start: int,
    x_stop: int,
    y: int,
    band_dbu: int,
) -> list[tuple[int, int]]:
    half = max(0, band_dbu // 2)
    band = pya.Region(pya.Box(x_start, y - half, x_stop, y + max(1, band_dbu - half)))
    cross = region & band
    cross.merge()

    intervals: list[tuple[int, int]] = []
    for polygon in cross.each_merged():
        box = polygon.bbox()
        if box.right > box.left:
            intervals.append((box.left, box.right))
    intervals.sort()
    return intervals


def occupancy_at(
    x: int,
    intervals: list[tuple[int, int]],
    cursor: int,
    right_closed: bool,
) -> tuple[int, int]:
    while cursor < len(intervals) and (
        intervals[cursor][1] < x if right_closed else intervals[cursor][1] <= x
    ):
        cursor += 1
    occupied = 0
    if cursor < len(intervals):
        left, right = intervals[cursor]
        if left <= x and (x <= right if right_closed else x < right):
            occupied = 1
    return occupied, cursor


def main() -> int:
    gds_path = os.path.abspath(require_rd("gds"))
    out_path = os.path.abspath(require_rd("out"))
    x_start_um = as_float("x_start_um")
    x_stop_um = as_float("x_stop_um")
    dx_um = as_float("dx_um")
    y_um = as_float("y_um", 0.0)
    layer_num = as_int("layer", 1)
    datatype_num = as_int("datatype", 0)
    band_dbu = as_int("band_dbu", 1)
    right_closed = as_bool("right_closed", False)
    requested_cell = rd("cell")

    if dx_um <= 0:
        raise ValueError("dx_um must be positive")
    if x_stop_um < x_start_um:
        raise ValueError("x_stop_um must be greater than or equal to x_start_um")

    layout = pya.Layout()
    layout.read(gds_path)
    dbu_um = layout.dbu
    if dbu_um <= 0:
        raise ValueError("Input layout has invalid dbu")

    if requested_cell not in (None, ""):
        cell = layout.cell(str(requested_cell))
        if cell is None:
            raise ValueError(f"Cell not found: {requested_cell}")
    else:
        cell = layout.top_cell()
        if cell is None:
            raise ValueError("Layout has no top cell")

    x_start = to_dbu(x_start_um, dbu_um)
    x_stop = to_dbu(x_stop_um, dbu_um)
    y = to_dbu(y_um, dbu_um)
    dx = to_dbu(dx_um, dbu_um)
    if dx <= 0:
        raise ValueError("dx_um rounds to zero dbu; use a larger dx or smaller dbu")

    sample_count = int(math.floor((x_stop - x_start) / dx)) + 1
    region = merged_layer_region(layout, cell, layer_num, datatype_num)
    band_x_stop = x_stop if right_closed else x_stop + dx
    intervals = intervals_from_band(region, x_start, band_x_stop, y, max(1, band_dbu))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    cursor = 0
    occupied_count = 0
    with open(out_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["x_um", "occupancy"])
        for index in range(sample_count):
            x = x_start + index * dx
            occupied, cursor = occupancy_at(x, intervals, cursor, right_closed)
            occupied_count += occupied
            writer.writerow([f"{from_dbu(x, dbu_um):.12g}", occupied])

    print(
        "wrote {out} samples={samples} occupied={occupied} layer={layer}/{datatype} "
        "cell={cell} dbu_um={dbu} right_closed={right_closed}".format(
            out=out_path,
            samples=sample_count,
            occupied=occupied_count,
            layer=layer_num,
            datatype=datatype_num,
            cell=cell.name,
            dbu=dbu_um,
            right_closed=right_closed,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
