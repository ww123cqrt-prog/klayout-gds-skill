#!/usr/bin/env python3
"""Launch KLayout embedded Python scripts in a repeatable way."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys


MACOS_CANDIDATES = (
    "/Applications/KLayout.app/Contents/MacOS/klayout",
    "/Applications/klayout.app/Contents/MacOS/klayout",
)


def find_klayout(explicit: str | None = None) -> str:
    candidates: list[str] = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("KLAYOUT_BIN"):
        candidates.append(os.environ["KLAYOUT_BIN"])
    path_hit = shutil.which("klayout")
    if path_hit:
        candidates.append(path_hit)
    candidates.extend(MACOS_CANDIDATES)

    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        path = Path(candidate).expanduser()
        if path.is_file() and os.access(path, os.X_OK):
            return str(path)

    checked = "\n  ".join(candidates) if candidates else "(none)"
    raise SystemExit(
        "Could not find a KLayout executable. Set KLAYOUT_BIN or pass --klayout.\n"
        f"Checked:\n  {checked}"
    )


def validate_vars(items: list[str]) -> list[str]:
    validated: list[str] = []
    for item in items:
        if "=" not in item:
            raise SystemExit(f"--var must be NAME=VALUE, got: {item!r}")
        name, _value = item.split("=", 1)
        if not name or any(ch.isspace() for ch in name):
            raise SystemExit(f"Invalid -rd variable name: {name!r}")
        validated.append(item)
    return validated


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a .py macro through KLayout's embedded Python interpreter."
    )
    parser.add_argument("script", help="KLayout Python macro (.py) to execute")
    parser.add_argument(
        "--var",
        "-D",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Variable passed to the macro via KLayout -rd. Repeat as needed.",
    )
    parser.add_argument("--klayout", help="Path to the KLayout executable")
    parser.add_argument("--cwd", help="Working directory for the KLayout process")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Run with the GUI instead of KLayout batch mode.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command that would run, then exit.",
    )
    args = parser.parse_args()

    script = Path(args.script).expanduser().resolve()
    if not script.is_file():
        raise SystemExit(f"Macro does not exist: {script}")
    if script.suffix.lower() != ".py":
        raise SystemExit(
            f"KLayout chooses the macro interpreter from the suffix; use a .py file: {script}"
        )

    klayout = find_klayout(args.klayout)
    rd_vars = validate_vars(args.var)

    cmd = [klayout]
    if not args.gui:
        cmd.append("-b")
    for item in rd_vars:
        cmd.extend(["-rd", item])
    cmd.extend(["-r", str(script)])

    print("+ " + shlex.join(cmd), flush=True)
    if args.dry_run:
        return 0

    completed = subprocess.run(cmd, cwd=args.cwd)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())
