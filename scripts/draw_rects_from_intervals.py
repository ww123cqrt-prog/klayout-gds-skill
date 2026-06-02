"""KLayout embedded-Python macro: draw x intervals as layout rectangles."""

from __future__ import annotations

import os
import re
import sys

import pya


def rd(name: str, default: object | None = None) -> object | None:
    return globals().get(name, default)


def require_rd(name: str) -> str:
    value = rd(name)
    if value is None or str(value) == "":
        raise ValueError(f"Missing required -rd variable: {name}")
    return str(value)


def as_float(name: str, default: float) -> float:
    value = rd(name, default)
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


def parse_intervals(path: str, start_col: int | None, end_col: int | None) -> list[tuple[float, float]]:
    intervals: list[tuple[float, float]] = []
    splitter = re.compile(r"[,;\s]+")

    with open(path, "r", encoding="utf-8-sig") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            fields = [field for field in splitter.split(line) if field]
            if not fields:
                continue

            try:
                if start_col is not None and end_col is not None:
                    x0 = float(fields[start_col])
                    x1 = float(fields[end_col])
                else:
                    numeric = []
                    for field in fields:
                        try:
                            numeric.append(float(field))
                        except ValueError:
                            pass
                    if len(numeric) < 2:
                        if not intervals:
                            continue
                        raise ValueError("line does not contain two numeric columns")
                    x0, x1 = numeric[0], numeric[1]
            except Exception as exc:
                if not intervals:
                    continue
                raise ValueError(f"Could not parse interval at {path}:{line_number}: {raw.rstrip()}") from exc

            if x1 < x0:
                x0, x1 = x1, x0
            intervals.append((x0, x1))

    return intervals


def main() -> int:
    intervals_path = os.path.abspath(require_rd("intervals"))
    out_path = os.path.abspath(require_rd("out"))
    width_um = as_float("width_um", 2.5)
    y_center_um = as_float("y_center_um", 0.0)
    x_scale = as_float("x_scale", 1.0)
    x_offset_um = as_float("x_offset_um", 0.0)
    dbu_um = as_float("dbu_um", 0.001)
    min_width_um = as_float("min_width_um", 0.0)
    layer_num = as_int("layer", 1)
    datatype_num = as_int("datatype", 0)
    merge_shapes = as_bool("merge", True)
    cell_name = str(rd("cell", "TOP"))

    start_col_value = rd("start_col")
    end_col_value = rd("end_col")
    start_col = int(start_col_value) if start_col_value not in (None, "") else None
    end_col = int(end_col_value) if end_col_value not in (None, "") else None
    if (start_col is None) != (end_col is None):
        raise ValueError("Set both start_col and end_col, or neither")

    if width_um <= 0:
        raise ValueError("width_um must be positive")
    if dbu_um <= 0:
        raise ValueError("dbu_um must be positive")

    source_intervals = parse_intervals(intervals_path, start_col, end_col)

    layout = pya.Layout()
    layout.dbu = dbu_um
    top = layout.create_cell(cell_name)
    layer_index = layout.layer(layer_num, datatype_num)
    shapes = top.shapes(layer_index)

    y0 = to_dbu(y_center_um - width_um / 2.0, dbu_um)
    y1 = to_dbu(y_center_um + width_um / 2.0, dbu_um)
    boxes: list[pya.Box] = []
    skipped = 0

    for raw_x0, raw_x1 in source_intervals:
        x0_um = raw_x0 * x_scale + x_offset_um
        x1_um = raw_x1 * x_scale + x_offset_um
        if x1_um < x0_um:
            x0_um, x1_um = x1_um, x0_um
        if x1_um - x0_um <= min_width_um:
            skipped += 1
            continue
        x0 = to_dbu(x0_um, dbu_um)
        x1 = to_dbu(x1_um, dbu_um)
        if x1 <= x0:
            skipped += 1
            continue
        boxes.append(pya.Box(x0, y0, x1, y1))

    if merge_shapes:
        region = pya.Region()
        for box in boxes:
            region.insert(box)
        region.merge()
        for polygon in region.each_merged():
            shapes.insert(polygon)
    else:
        for box in boxes:
            shapes.insert(box)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    layout.write(out_path)
    print(
        "wrote {out} intervals={intervals} drawn={drawn} skipped={skipped} "
        "layer={layer}/{datatype} width_um={width} dbu_um={dbu}".format(
            out=out_path,
            intervals=len(source_intervals),
            drawn=len(boxes),
            skipped=skipped,
            layer=layer_num,
            datatype=datatype_num,
            width=width_um,
            dbu=dbu_um,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
