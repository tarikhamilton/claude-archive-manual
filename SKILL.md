---
name: archive-manual
description: Find official instruction manuals or user guides online, download them to the user's manuals directory, maintain a JSON index, and keep MANUALS.md up to date. Use when the user wants to save, find, archive, or download an instruction manual or user guide for any product — or mentions wanting to toss/throw away a physical manual or booklet. Also triggers when the user lists multiple products with manuals to archive.
---

# Archive Manual

Find official instruction manuals online and save them to the user's manuals directory.

## Destination

The destination is the directory referenced by the `CLAUDE_MANUALS_DIR` environment variable. If it is not set, default to `$HOME/Manuals/`. Create the directory if it doesn't exist.

In every shell command in this skill, use the form `"${CLAUDE_MANUALS_DIR:-$HOME/Manuals}"` so the env var is read at execution time and the default works without setup.

File naming: kebab-case, always .pdf
Good: `polar-h10-user-manual.pdf`, `sonoff-swv-zigbee-water-valve-manual.pdf`
Avoid: `manual.pdf`, `H10_Manual.pdf`, names with spaces

## Multiple products
If the user lists several products, search for all in parallel, then download sequentially.

---

## Step 1: Find the PDF

Search for "[product name] user manual PDF" and "[product name] instruction manual filetype:pdf".

Source priority:
1. Official manufacturer support pages
2. Direct PDF links from manufacturer-owned domains
3. ManualsLib — reliable archive, great fallback
4. Other hosting sites (manuals.plus, manualzz.com)

Get at least two URLs per manual: primary + fallback. Third-party hosts go down.

---

## Step 2: Download directly

Claude Code bash has full network access. Download directly:

```bash
DIR="${CLAUDE_MANUALS_DIR:-$HOME/Manuals}"
mkdir -p "$DIR"
FILE="$DIR/filename.pdf"

# Check if already exists first
if [ -s "$FILE" ]; then
  echo "Already exists, skipping"
else
  curl -L -o "$FILE" "PRIMARY_URL" --max-time 60 -s
  # If that fails, try fallback:
  [ -s "$FILE" ] || curl -L -o "$FILE" "FALLBACK_URL" --max-time 60 -s
fi
```

Verify the downloaded file is a real PDF (`head -c 4 "$FILE"` should return `%PDF`) before considering it successful. HTML error pages frequently come back as 200s.

Status: `downloaded` if curl succeeded AND the file is a real PDF, `manual-download` if no direct PDF exists anywhere.

For `manual-download` cases, tell the user the ManualsLib URL and the exact filename to save as.

---

## Step 3: Update the index

Read `"${CLAUDE_MANUALS_DIR:-$HOME/Manuals}/.manuals-index.json"`. Create if missing:

```json
{"manuals": [], "artifact_id": null}
```

Add or update entry:

```json
{
  "filename": "polar-h10-user-manual.pdf",
  "product": "Polar H10 Heart Rate Monitor",
  "source_url": "https://...",
  "source_name": "Polar Official Support",
  "date_saved": "YYYY-MM-DD",
  "status": "downloaded"
}
```

Write back before moving on.

---

## Step 4: Regenerate the HTML summary

After updating the index, write `"${CLAUDE_MANUALS_DIR:-$HOME/Manuals}/MANUALS.html"` — a self-contained, sortable, filterable browser view of all manuals.

The template lives alongside this skill at `templates/MANUALS.template.html`. To regenerate:

1. Read the template file (path: this skill folder + `templates/MANUALS.template.html`).
2. Read the index at `"${CLAUDE_MANUALS_DIR:-$HOME/Manuals}/.manuals-index.json"`.
3. Replace the literal placeholder `__MANUALS_DATA__` in the template with `JSON.stringify(index.manuals, null, 2)`. There is exactly one occurrence — do not touch anything else.
4. Write the result to `"${CLAUDE_MANUALS_DIR:-$HOME/Manuals}/MANUALS.html"`, overwriting any existing file.

The page handles its own sorting (click column headers), filtering (top-of-page search box), stats line, dark mode, and link rendering. No build step, no external dependencies, single self-contained file.

If a stale `MANUALS.md` exists in the same directory, delete it — the HTML replaces it.

---

## Finishing up

Keep the response brief:
- One line per product: what you found and where
- Whether it downloaded or needs manual action
- Done — no narrating every step
