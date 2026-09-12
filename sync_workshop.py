#!/usr/bin/env python3
"""Seed per-mod translations from installed Steam Workshop locales."""

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).parent
TRANSLATIONS_DIR = ROOT / "Translations"


class ObjectPairs(list):
    pass


def load_object(path: Path, *, normalize_keys: bool) -> dict[str, str]:
    with path.open(encoding="utf-8-sig") as source:
        pairs = json.load(source, object_pairs_hook=ObjectPairs)
    if not isinstance(pairs, ObjectPairs):
        raise ValueError(f"{path}: root must be a JSON object")

    result: dict[str, str] = {}
    for key, value in pairs:
        if not isinstance(key, str) or not isinstance(value, str):
            raise ValueError(f"{path}: keys and values must be strings")
        normalized_key = key.strip().lower()
        if not normalized_key:
            raise ValueError(f"{path}: key must not be empty")
        if not normalize_keys and key != normalized_key:
            raise ValueError(f"{path}: key must be lowercase and trimmed: {key!r}")
        if normalized_key in result:
            raise ValueError(f"{path}: duplicate key after normalization: {key!r}")
        result[normalized_key] = value
    return result


def translation_name(mod_dir: Path) -> str:
    dlls = sorted(
        path for path in mod_dir.iterdir() if path.is_file() and path.suffix.lower() == ".dll"
    )
    if len(dlls) != 1:
        raise ValueError(f"expected exactly one root DLL, found {len(dlls)}")
    slug = re.sub(r"[^a-z0-9._-]+", "-", dlls[0].stem.lower()).strip("-")
    return f"{slug or mod_dir.name}.json"


def expected_translation(
    source: dict[str, str], bundled_ja: dict[str, str], existing: dict[str, str]
) -> dict[str, str]:
    result = dict(source)
    result.update(bundled_ja)
    for key, value in existing.items():
        if key not in source or value != source[key]:
            result[key] = value
    return result


def write_json(path: Path, values: dict[str, str]) -> None:
    content = json.dumps(values, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workshop-dir", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    if not args.workshop_dir.is_dir():
        raise SystemExit(f"Workshop directory not found: {args.workshop_dir}")

    changed: list[str] = []
    destination_owners: dict[str, str] = {}
    scanned = 0
    TRANSLATIONS_DIR.mkdir(exist_ok=True)

    for mod_dir in sorted(path for path in args.workshop_dir.iterdir() if path.is_dir()):
        source_path = mod_dir / "Locales" / "en.json"
        if not source_path.is_file():
            continue
        try:
            destination = TRANSLATIONS_DIR / translation_name(mod_dir)
        except ValueError as error:
            print(f"Skipped {mod_dir.name}: {error}")
            continue

        if destination.name in destination_owners:
            raise SystemExit(
                f"Translation filename collision: Workshop items "
                f"{destination_owners[destination.name]} and {mod_dir.name} both map to "
                f"{destination.name}"
            )
        destination_owners[destination.name] = mod_dir.name

        source = load_object(source_path, normalize_keys=True)
        bundled_ja_path = mod_dir / "Locales" / "ja.json"
        bundled_ja = (
            load_object(bundled_ja_path, normalize_keys=True)
            if bundled_ja_path.is_file()
            else {}
        )
        existing = (
            load_object(destination, normalize_keys=False) if destination.exists() else {}
        )
        expected = expected_translation(source, bundled_ja, existing)
        scanned += 1

        if expected != existing:
            changed.append(destination.name)
            if not args.check:
                write_json(destination, expected)
            added = len(expected.keys() - existing.keys())
            refreshed = sum(
                key in existing and existing[key] != value
                for key, value in expected.items()
            )
            print(f"{'Outdated' if args.check else 'Updated'} {destination.name}: "
                  f"added {added}, refreshed {refreshed} keys")

    if args.check and changed:
        raise SystemExit("Workshop translations are outdated; run: make sync")
    print(f"OK: scanned {scanned} Workshop localization mod(s)")


if __name__ == "__main__":
    main()
