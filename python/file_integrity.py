#!/usr/bin/env python3
"""Create or check a SHA-256 baseline for files in an authorized local folder."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def snapshot(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): digest(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write-baseline", type=Path)
    group.add_argument("--check-baseline", type=Path)
    args = parser.parse_args()

    root = args.path.resolve()
    if not root.is_dir():
        parser.error(f"not a directory: {root}")
    current = snapshot(root)

    if args.write_baseline:
        args.write_baseline.write_text(json.dumps(current, indent=2) + "\n", encoding="utf-8")
        print(f"baseline written: {len(current)} file(s)")
        return 0

    expected = json.loads(args.check_baseline.read_text(encoding="utf-8"))
    added = sorted(set(current) - set(expected))
    removed = sorted(set(expected) - set(current))
    changed = sorted(name for name in set(current) & set(expected) if current[name] != expected[name])
    for label, names in (("ADDED", added), ("REMOVED", removed), ("CHANGED", changed)):
        for name in names:
            print(f"{label}: {name}")
    print(f"checked {len(current)} file(s)")
    return 1 if added or removed or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
