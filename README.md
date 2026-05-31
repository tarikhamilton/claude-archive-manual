# archive-manual

A [Claude Code](https://docs.claude.com/claude-code) skill that finds official instruction manuals online, downloads them to a local directory, keeps a JSON index, and regenerates a `MANUALS.md` summary table.

Trigger it by mentioning a product manual you want to save, archive, or download — or by saying you want to toss/throw away a physical manual. The skill handles search, download, indexing, and summary regeneration in one pass.

## Install

Drop the `archive-manual/` folder into `~/.claude/skills/`:

```bash
git clone https://github.com/<owner>/archive-manual.git ~/.claude/skills/archive-manual
```

Or hand the SKILL.md URL to Claude and ask it to install — it'll figure out the right path.

## Configuration

The skill saves manuals to whichever directory `CLAUDE_MANUALS_DIR` points at. If the env var is unset, it defaults to `~/Manuals/`.

To use a different directory (e.g. a synced cloud folder), set the env var in your Claude Code settings — `~/.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_MANUALS_DIR": "/Users/you/Dropbox/Manuals"
  }
}
```

Or in your shell rc (`~/.zshrc`, `~/.bashrc`):

```bash
export CLAUDE_MANUALS_DIR="$HOME/Dropbox/Manuals"
```

Both work. The `settings.json` route scopes the variable to Claude Code only. The shell rc route makes it available system-wide.

## What it produces

Inside the manuals directory:

```
<CLAUDE_MANUALS_DIR>/
├── .manuals-index.json     ← source of truth, one entry per manual
├── MANUALS.html            ← sortable + filterable browser view (open in any browser)
└── *.pdf                   ← the manuals themselves (kebab-case filenames)
```

The JSON index tracks each manual's product name, filename, source URL, date saved, and status (`downloaded` or `manual-download` — the latter for cases where no direct PDF exists and the user has to grab it themselves).

`MANUALS.html` is a self-contained page (vanilla JS, no external dependencies, dark-mode aware) generated from the index. Open it in any browser. Click column headers to sort, type in the search box to filter, click filenames to open the PDFs.

## Use

Just talk to Claude:

> "Save the manual for my Polar H10."
>
> "I want to throw out the Ninja NC501 Creami Deluxe manual."
>
> "Archive manuals for: Bosch 1617 router, Epson ET-8500, LG WM3500CW washer."

Multiple products in one request are handled in parallel.

## License

MIT.
