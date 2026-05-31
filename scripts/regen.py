#!/usr/bin/env python3
"""Regenerate MANUALS.html from .manuals-index.json + the template.

Pure transform: read the index, read the template, substitute the data
placeholder, write the HTML. No LLM judgment, no network.

Usage:
    python3 regen.py

Reads CLAUDE_MANUALS_DIR (or ~/Manuals) for the index + output location.
The template is resolved relative to this script: ../templates/MANUALS.template.html.
"""
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATE = SKILL_DIR / "templates" / "MANUALS.template.html"
PLACEHOLDER = "__MANUALS_DATA__"


def main() -> None:
    dir_ = Path(os.environ.get("CLAUDE_MANUALS_DIR") or (Path.home() / "Manuals"))
    index_path = dir_ / ".manuals-index.json"
    out_path = dir_ / "MANUALS.html"

    if not index_path.exists():
        sys.exit(f"No index at {index_path}")
    if not TEMPLATE.exists():
        sys.exit(f"No template at {TEMPLATE}")

    index = json.loads(index_path.read_text())
    manuals = index.get("manuals", [])
    template = TEMPLATE.read_text()

    placeholder_count = template.count(PLACEHOLDER)
    if placeholder_count != 1:
        sys.exit(
            f"Expected exactly one {PLACEHOLDER} in template, found {placeholder_count}"
        )

    html = template.replace(
        PLACEHOLDER, json.dumps(manuals, indent=2, ensure_ascii=False)
    )

    tmp = out_path.with_suffix(".html.tmp")
    tmp.write_text(html)
    tmp.replace(out_path)

    print(f"Regenerated {out_path} ({len(html)} bytes, {len(manuals)} manuals)")


if __name__ == "__main__":
    main()
