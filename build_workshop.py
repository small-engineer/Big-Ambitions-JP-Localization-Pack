#!/usr/bin/env python3
"""Build the Steam Workshop description and upload VDF."""

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).parent
METADATA_FILE = ROOT / "workshop" / "metadata.json"
DESCRIPTION_FILE = ROOT / "workshop" / "description.txt"


def load_metadata() -> dict:
    with METADATA_FILE.open(encoding="utf-8") as source:
        metadata = json.load(source)
    if not isinstance(metadata, dict):
        raise ValueError("workshop/metadata.json must contain a JSON object")
    for key in ("appId", "title", "summary", "supportedMods", "usage", "notes"):
        if key not in metadata:
            raise ValueError(f"workshop/metadata.json is missing {key!r}")
    if not str(metadata["appId"]).isdigit():
        raise ValueError("appId must be numeric")

    listed_files = [mod.get("translationFile") for mod in metadata["supportedMods"]]
    if any(not isinstance(name, str) or not name for name in listed_files):
        raise ValueError("each supported mod must define translationFile")
    if len(listed_files) != len(set(listed_files)):
        raise ValueError("supported mod translationFile values must be unique")
    translation_files = {
        path.name for path in (ROOT / "Translations").glob("*.json")
    }
    if set(listed_files) != translation_files:
        missing = sorted(translation_files - set(listed_files))
        stale = sorted(set(listed_files) - translation_files)
        raise ValueError(
            "supported mod list differs from Translations "
            f"(missing={missing}, stale={stale})"
        )
    return metadata


def workshop_link(item: dict) -> str:
    name = item["name"]
    workshop_id = str(item["workshopItemId"])
    if not workshop_id.isdigit():
        raise ValueError(f"Workshop item ID for {name!r} must be numeric")
    return (
        "[url=https://steamcommunity.com/sharedfiles/filedetails/"
        f"?id={workshop_id}]{name}[/url]"
    )


def render_description(metadata: dict) -> str:
    lines = [f"[h1]{metadata['title']}[/h1]", *metadata["summary"], "", "[h2]対応 Mod[/h2]", "[list]"]
    for mod in metadata["supportedMods"]:
        line = f"[*]{workshop_link(mod)} — {mod['details']}"
        dependencies = mod.get("dependencies", [])
        if dependencies:
            line += " 必須 Mod: " + ", ".join(workshop_link(item) for item in dependencies)
        lines.append(line)
    lines.extend(["[/list]", "", "[h2]導入方法[/h2]", "[list]"])
    lines.extend(f"[*]{step}" for step in metadata["usage"])
    lines.extend(["[/list]", "", "[h2]注意事項[/h2]", "[list]"])
    lines.extend(f"[*]{note}" for note in metadata["notes"])
    lines.extend(["[/list]", ""])
    return "\n".join(lines)


def quote_vdf(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "\\n")
    return f'"{escaped}"'


def write_vdf(args: argparse.Namespace, metadata: dict, description: str) -> None:
    if not args.published_file_id or not args.published_file_id.isdigit():
        raise ValueError("--published-file-id must be numeric")
    required_paths = (args.content_folder, args.preview_file)
    if any(path is None for path in required_paths) or args.change_note is None:
        raise ValueError(
            "--vdf requires --content-folder, --preview-file, and --change-note"
        )

    fields = {
        "appid": str(metadata["appId"]),
        "publishedfileid": args.published_file_id,
        "contentfolder": str(args.content_folder),
        "previewfile": str(args.preview_file),
        "title": metadata["title"],
        "description": description,
        "changenote": args.change_note,
    }
    lines = ['"workshopitem"', "{"]
    lines.extend(f"  {quote_vdf(key)} {quote_vdf(value)}" for key, value in fields.items())
    lines.extend(["}", ""])
    args.vdf.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--vdf", type=Path)
    parser.add_argument("--published-file-id")
    parser.add_argument("--content-folder", type=Path)
    parser.add_argument("--preview-file", type=Path)
    parser.add_argument("--change-note")
    args = parser.parse_args()

    metadata = load_metadata()
    description = render_description(metadata)

    if args.vdf:
        write_vdf(args, metadata, description)
    elif args.check:
        if not DESCRIPTION_FILE.exists() or DESCRIPTION_FILE.read_text(encoding="utf-8") != description:
            raise SystemExit("workshop/description.txt is outdated; run: make workshop")
        print(f"OK: {DESCRIPTION_FILE.relative_to(ROOT)}")
    else:
        DESCRIPTION_FILE.write_text(description, encoding="utf-8")
        print(f"Wrote {DESCRIPTION_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
