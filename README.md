# archive-manual

A [Claude Code](https://docs.claude.com/claude-code) skill that finds official instruction manuals online, downloads them to a local directory, AI-enriches each entry with a summary + spec sheet + troubleshooting list, keeps a JSON index, and regenerates a sortable + filterable browser view.

Trigger it by mentioning a product manual you want to save, archive, or download — or by saying you want to toss/throw away a physical manual. The skill handles search, download, indexing, enrichment, and summary regeneration in one pass.

## Install

Drop the `archive-manual/` folder into `~/.claude/skills/`:

```bash
git clone https://github.com/tarikhamilton/claude-archive-manual.git ~/.claude/skills/archive-manual
```

Or hand the SKILL.md URL to Claude and ask it to install — it'll figure out the right path.

## Requirements

- Python 3 (ships with macOS; nothing to install)
- `pdftotext` (Poppler), **optional** — only needed for full-text PDF search. Install with `brew install poppler`. Without it, search still works across product / file / source / summary / specs / troubleshooting; just not across the raw PDF body.

## Configuration

All settings are environment variables. Set them in your Claude Code settings — `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_MANUALS_DIR": "/Users/you/Dropbox/Manuals",
    "CLAUDE_MANUALS_AUTO_ENRICH": "true"
  }
}
```

Or in your shell rc (`~/.zshrc`, `~/.bashrc`) for system-wide use.

| Variable | Default | What it does |
|---|---|---|
| `CLAUDE_MANUALS_DIR` | `~/Manuals` | Where manuals + the index + the HTML page live. |
| `CLAUDE_MANUALS_AUTO_ENRICH` | `true` | When `true` (or unset), each archive runs an AI-extraction pass to populate summary, specs, key features, and troubleshooting. Set to `false`, `0`, `no`, or `off` to disable globally. |

You can also opt out of enrichment for a single request by including phrases like "skip enrichment", "just save the file", "no summary", or "minimal" in your prompt.

## What it produces

Inside the manuals directory:

```
<CLAUDE_MANUALS_DIR>/
├── .manuals-index.json     ← source of truth, one entry per manual
├── MANUALS.html            ← sortable, filterable, expandable browser view
└── *.pdf                   ← the manuals themselves (kebab-case filenames)
```

`MANUALS.html` is a self-contained page (vanilla JS, no external dependencies, dark-mode aware). Open it in any browser. Click column headers to sort, type in the search box to filter across all fields, click any row to expand its detail panel (summary, specs, key features as chips, troubleshooting as nested accordion). Click filenames to open the PDFs.

## How it works

The skill ships three small helper scripts that handle the deterministic operations — JSON mutation, HTML regeneration, PDF text extraction. The skill body itself handles the LLM-judgment parts (web search, PDF reading + summarization, opt-out phrase recognition).

```
archive-manual/
├── SKILL.md
├── README.md
├── scripts/
│   ├── upsert.py           ← atomic merge-by-filename into .manuals-index.json
│   ├── regen.py            ← stamp the JSON into the HTML template
│   └── extract-text.sh     ← pdftotext wrapper, graceful fallback
└── templates/
    └── MANUALS.template.html
```

This split keeps the skill body shorter and means the model doesn't have to hand-roll JSON merges on every archive — the script does it deterministically.

## Use

Just talk to Claude:

> "Save the manual for my Polar H10."
>
> "I want to throw out the Ninja NC501 Creami Deluxe manual."
>
> "Archive manuals for: Bosch 1617 router, Epson ET-8500, LG WM3500CW washer."
>
> "Re-enrich the Ninja one."
>
> "Save the manual for X — just the file, skip enrichment."

Multiple products in one request are handled in parallel.

## License

MIT.
