#!/usr/bin/env python3
"""Upsert an entry into .manuals-index.json by filename.

Reads a JSON object from stdin. Required fields: filename, product, status.
Optional fields: source_url, source_name, date_saved (defaults to today for
new entries), enriched_at, summary, specs, key_features, troubleshooting,
full_text.

If an entry with the same filename already exists, the passed fields are
merged into it — fields not in the payload are preserved. Otherwise a new
entry is appended. Writes are atomic (tmp file + rename).

Usage:
    echo '{"filename": "foo.pdf", "product": "Foo", "status": "downloaded"}' \
        | python3 upsert.py

Reads CLAUDE_MANUALS_DIR (or ~/Manuals) for the index location.
"""
import datetime
import json
import os
import sys
from pathlib import Path

REQUIRED = {"filename", "product", "status"}
ALLOWED = REQUIRED | {
    "source_url",
    "source_name",
    "date_saved",
    "enriched_at",
    "summary",
    "specs",
    "key_features",
    "troubleshooting",
    "full_text",
}


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as exc:
        sys.exit(f"Invalid JSON on stdin: {exc}")

    if not isinstance(payload, dict):
        sys.exit("Expected a JSON object on stdin.")

    unknown = set(payload) - ALLOWED
    if unknown:
        sys.exit(f"Unknown fields: {sorted(unknown)}")

    missing = REQUIRED - set(payload)
    if missing:
        sys.exit(f"Missing required fields: {sorted(missing)}")

    dir_ = Path(os.environ.get("CLAUDE_MANUALS_DIR") or (Path.home() / "Manuals"))
    dir_.mkdir(parents=True, exist_ok=True)
    index_path = dir_ / ".manuals-index.json"

    if index_path.exists():
        index = json.loads(index_path.read_text())
    else:
        index = {"manuals": [], "artifact_id": None}

    manuals = index.setdefault("manuals", [])
    filename = payload["filename"]

    existing = next((m for m in manuals if m.get("filename") == filename), None)
    if existing is not None:
        existing.update(payload)
        action = "updated"
    else:
        payload.setdefault("date_saved", datetime.date.today().isoformat())
        manuals.append(payload)
        action = "added"

    tmp = index_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(index_path)

    print(f"{action}: {filename}")


if __name__ == "__main__":
    main()
