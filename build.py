#!/usr/bin/env python3
"""Validate and merge per-mod Japanese localization files."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).parent
SOURCE_DIR = ROOT / "Translations"
OUTPUT_FILE = ROOT / "Locales" / "ja.json"


class ObjectPairs(list):
    pass


def build() -> str:
    merged: dict[str, str] = {}
    owners: dict[str, str] = {}

    for path in sorted(SOURCE_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as source:
            entries = json.load(source, object_pairs_hook=ObjectPairs)
        if not isinstance(entries, ObjectPairs):
            raise ValueError(f"{path.name}: root must be a JSON object")

        for key, value in entries:
            if not isinstance(key, str) or not isinstance(value, str):
                raise ValueError(f"{path.name}: keys and values must be strings")
            if not key or key != key.strip().lower():
                raise ValueError(f"{path.name}: key must be lowercase and trimmed: {key!r}")
            if key in merged:
                raise ValueError(
                    f"duplicate key {key!r}: {owners[key]} and {path.name}"
                )
            merged[key] = value
            owners[key] = path.name

    return json.dumps(merged, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check", action="store_true", help="fail if Locales/ja.json is outdated"
    )
    args = parser.parse_args()
    content = build()

    if args.check:
        if not OUTPUT_FILE.exists() or OUTPUT_FILE.read_text(encoding="utf-8") != content:
            raise SystemExit("Locales/ja.json is outdated; run: python3 build.py")
        print(f"OK: {OUTPUT_FILE.relative_to(ROOT)}")
        return

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
