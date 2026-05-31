---
name: archive-manual
description: Find official instruction manuals or user guides online, download them to the user's manuals directory, maintain a JSON index, and keep MANUALS.html up to date. Use when the user wants to save, find, archive, or download an instruction manual or user guide for any product — or mentions wanting to toss/throw away a physical manual or booklet. Also triggers when the user lists multiple products with manuals to archive.
---

# Archive Manual

Find official instruction manuals online, save them locally, index them, and regenerate a sortable + filterable browser view.

## Skill layout

This skill ships three helper scripts that handle the deterministic operations (JSON mutation, HTML regeneration, PDF text extraction). The skill body handles the LLM-judgment parts (web search, PDF reading + summarization, opt-out recognition).

```
~/.claude/skills/archive-manual/
├── SKILL.md                       ← this file
├── scripts/
│   ├── upsert.py                  ← mutate .manuals-index.json by filename
│   ├── regen.py                   ← regenerate MANUALS.html from index + template
│   └── extract-text.sh            ← pdftotext wrapper for full-text search
└── templates/
    └── MANUALS.template.html      ← the page template
```

All scripts read `CLAUDE_MANUALS_DIR` (default `$HOME/Manuals`) to find the index + write the HTML output.

## Destination

Save manuals to `${CLAUDE_MANUALS_DIR:-$HOME/Manuals}`. Create the directory if missing.

File naming: kebab-case, always `.pdf`.
Good: `polar-h10-user-manual.pdf`, `sonoff-swv-zigbee-water-valve-manual.pdf`
Avoid: `manual.pdf`, `H10_Manual.pdf`, names with spaces.

## Multiple products

If the user lists several products, search for all in parallel, then process sequentially (one full pipeline per product).

---

## Step 1: Find the PDF

Search for `"<product name>" user manual PDF` and `"<product name>" instruction manual filetype:pdf`. Source priority:

1. Official manufacturer support pages
2. Direct PDF links from manufacturer-owned domains
3. ManualsLib — reliable archive, great fallback
4. Other hosting sites (manuals.plus, manualzz.com)

Capture a primary URL and a fallback URL. Third-party hosts go down.

---

## Step 2: Download

```bash
DIR="${CLAUDE_MANUALS_DIR:-$HOME/Manuals}"
mkdir -p "$DIR"
FILE="$DIR/<filename>.pdf"

if [ -s "$FILE" ]; then
  echo "Already exists, skipping download"
else
  curl -L -o "$FILE" "<PRIMARY_URL>" --max-time 60 -s
  [ -s "$FILE" ] || curl -L -o "$FILE" "<FALLBACK_URL>" --max-time 60 -s
fi

# Verify it's actually a PDF (HTML error pages frequently return 200)
if [ "$(head -c 4 "$FILE" 2>/dev/null)" != "%PDF" ]; then
  rm -f "$FILE"
  echo "Not a real PDF — both URLs returned non-PDF content"
fi
```

If both URLs fail, set status to `manual-download` (not `downloaded`) and tell the user the ManualsLib URL plus the kebab-case filename to save as. They'll grab it manually.

---

## Step 3: Upsert the index entry

Build a JSON object with the core fields and pipe to `upsert.py`. Required: `filename`, `product`, `status`. Add `source_url` and `source_name` when known.

```bash
cat <<'JSON' | python3 ~/.claude/skills/archive-manual/scripts/upsert.py
{
  "filename": "polar-h10-user-manual.pdf",
  "product": "Polar H10 Heart Rate Monitor",
  "source_url": "https://support.polar.com/...",
  "source_name": "Polar Official Support",
  "status": "downloaded"
}
JSON
```

The script:
- Creates `.manuals-index.json` if missing
- Upserts by `filename` — merges passed fields into an existing entry, preserves all other fields
- Defaults `date_saved` to today for new entries
- Writes atomically (tmp + rename)

---

## Step 4: Regenerate the HTML page

```bash
python3 ~/.claude/skills/archive-manual/scripts/regen.py
```

Reads the index + template, writes `MANUALS.html` to the manuals directory. Pure transform. No model judgment.

If a stale `MANUALS.md` exists in the same directory, delete it.

---

## Step 5: Enrich the entry

Auto-runs after Step 4 unless skipped (see "When to skip" below). Enrichment populates the optional fields so the HTML page can show a useful detail view per manual.

### What to extract (LLM judgment)

Read the PDF with the Read tool. For the first pass use `pages: "1-20"` — overview, specs, and TOC almost always live in the front matter.

1. **`summary`** — one paragraph (~50 words), present tense, plain prose describing what the product is and what it does.
2. **`specs`** — a JSON object containing only the keys the manual actually exposes. **Omit any key the manual doesn't cover. Do not invent values.** Common keys: `model`, `dimensions`, `weight`, `power`, `battery`, `warranty`, `customer_service`, `serial_location`.
3. **`key_features`** — 3-6 short chip-style strings, headline capabilities only.
4. **`troubleshooting`** — array of `{question, fix, page}`. Find the troubleshooting / FAQ / Common Issues section (use the TOC if present; otherwise scan later pages with the Read tool). `question` is the symptom in plain language. `fix` is one or two sentences. `page` is the PDF page number. Cap at ~10 entries; pick the highest-value ones if more exist.

### Full text (deterministic)

```bash
FULL_TEXT=$(bash ~/.claude/skills/archive-manual/scripts/extract-text.sh "<filename>.pdf" 2>/dev/null || echo "")
```

If `pdftotext` (Poppler) isn't installed, the script exits non-zero and `FULL_TEXT` ends up empty. Tell the user **once per session**: `Install Poppler for full-text search: brew install poppler`. Don't repeat the hint on every subsequent archive.

### Save the enrichment + regenerate

Pipe the enrichment payload to `upsert.py` (filename-keyed merge preserves the Step 3 fields), then re-run `regen.py`:

```bash
cat <<'JSON' | python3 ~/.claude/skills/archive-manual/scripts/upsert.py
{
  "filename": "polar-h10-user-manual.pdf",
  "product": "Polar H10 Heart Rate Monitor",
  "status": "downloaded",
  "enriched_at": "2026-05-31",
  "summary": "...",
  "specs": {"model": "...", "warranty": "..."},
  "key_features": ["...", "..."],
  "troubleshooting": [{"question": "...", "fix": "...", "page": 14}],
  "full_text": "..."
}
JSON

python3 ~/.claude/skills/archive-manual/scripts/regen.py
```

### When to skip enrichment

Don't run Step 5 if either is true:

- The environment variable `CLAUDE_MANUALS_AUTO_ENRICH` is set to `false`, `0`, `no`, or `off`.
- The user's prompt contains an opt-out phrase. Recognize these (case-insensitive substring match against the user's request):
  - "skip enrich" / "no enrich" / "don't enrich" / "without enrich"
  - "no summary" / "skip summary"
  - "just save" / "just the file" / "just the pdf"
  - "minimal" / "fast" / "quick"
  - "no details" / "no metadata"

When skipped, the entry has only the Step 3 fields. The HTML page still works — the detail panel shows "Not enriched yet."

### Re-enriching existing manuals

If the user says "re-enrich the Ninja one", "enrich my manuals", "fill in details for the LG washer", or similar, run Step 5 against the named (or all) manuals in the index — even if they already have `enriched_at`. The upsert script will merge the new values over the old ones.

---

## Finishing up

Keep the response brief:
- One line per product: what you found, where it saved, whether enrichment ran
- For `manual-download` cases, the ManualsLib URL and the exact kebab-case filename to save as
- Done — no narrating every step
