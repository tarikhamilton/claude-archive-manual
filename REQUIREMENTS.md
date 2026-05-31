# archive-manual — Requirements

## What it is

A Claude Code skill that finds the official PDF manual for any product, downloads it to a local archive directory, populates structured metadata about each entry via AI extraction, and regenerates a self-contained sortable + filterable HTML page that surfaces summary, specs, troubleshooting, and full-text search across all archived manuals.

The skill exists so that the paper version of a manual can be thrown away — both the file and a useful index of its content remain available locally and offline.

---

## Goals

- **One step from "I want this manual" to "it's filed."** Mentioning a product name in a Claude session triggers the skill; the user does not invoke it explicitly.
- **The archive is more useful than Finder.** Each entry exposes a one-paragraph summary, a spec sheet, a troubleshooting Q&A list, and full-text search across the PDF body — visible without opening the file.
- **Configuration is one env var.** The destination directory comes from `CLAUDE_MANUALS_DIR`. No other setup is required to use the skill.
- **The skill is portable.** Anyone clones the GitHub repo into `~/.claude/skills/archive-manual/` and the skill works. The only optional system dependency is Poppler (for full-text search content); the skill degrades gracefully without it.
- **The index file is the source of truth.** The HTML page is a derived presentation layer; deleting it does not lose data.

---

## Non-goals (explicit out of scope)

- **Multi-user / cloud sync.** A user's archive directory is local (or sync-folder-backed). The skill does not implement its own sync.
- **OCR for scanned PDFs.** The skill assumes the PDF contains a real text layer. Scanned-only manuals fall back to AI extraction from the PDF Read tool and an empty `full_text`.
- **Image-based content extraction.** Diagrams, exploded views, and parts numbers in images are not parsed.
- **Purchase metadata, location-in-home, warranty-end-date tracking.** Considered and deferred — see Future considerations.
- **Maintenance schedule integration.** Considered and deferred.
- **A backend or API.** The skill writes files to disk; there is no server.
- **Cross-LLM compatibility.** The skill targets Claude Code's skill runtime. The markdown content is portable in principle but the auto-trigger contract is Claude-specific.

---

## User flows

### Archive a single product

User says something like:
> "Save the manual for the Bosch 1617 router."

The skill:
1. Web-searches for the official manufacturer PDF (priority: manufacturer site → manufacturer-owned domains → ManualsLib → other archives). Captures a primary URL and a fallback URL.
2. Downloads to `${CLAUDE_MANUALS_DIR}/<kebab-case-filename>.pdf` and verifies the first 4 bytes are `%PDF`.
3. Pipes a core JSON payload (filename, product, source URL, source name, status) to `scripts/upsert.py`.
4. Runs `scripts/regen.py` to rebuild `MANUALS.html`.
5. Runs the enrichment pass (Step 5) unless opted out.

### Archive multiple products in one request

> "Archive manuals for: Polar H10, Sonoff SWV, Orbit Yard Enforcer."

Search runs in parallel; download + index + enrichment happen sequentially per product.

### Re-enrich an existing entry

> "Re-enrich the Ninja Creami one." / "Enrich my manuals."

Skill runs Step 5 against the named (or all) manuals in the index, overwriting any prior optional fields. Core fields (date saved, source URL) are preserved by the upsert's filename-keyed merge.

### Opt out of enrichment for one request

Recognized phrases in the user's prompt cause Step 5 to be skipped: "skip enrichment", "no summary", "just save the file", "minimal", "fast". The entry then has only the core fields; the detail panel in the HTML shows "Not enriched yet" until a later re-enrich.

### Browse the archive

User runs `open ${CLAUDE_MANUALS_DIR}/MANUALS.html` and gets a sortable + filterable table. Clicking a row expands a detail drawer with summary, spec list, key features (chips), and troubleshooting accordion. The top-of-page search box filters across product, filename, source, summary, specs, troubleshooting Q&A, and full PDF text.

### Manual-download fallback

When no direct PDF URL exists (some manufacturer pages, ManualsLib's login-gated PDFs), the skill records the entry with `status: "manual-download"` and tells the user the ManualsLib URL plus the exact kebab-case filename to save as. Re-running enrichment on that entry waits until the file appears on disk.

---

## Data model

The `.manuals-index.json` file at the archive root is the source of truth.

```jsonc
{
  "manuals": [
    {
      // Core fields — required, written at archive time
      "filename": "polar-h10-user-manual.pdf",     // primary key for upsert
      "product": "Polar H10 Heart Rate Monitor",
      "source_url": "https://...",
      "source_name": "Polar Official Support",
      "date_saved": "YYYY-MM-DD",
      "status": "downloaded",                       // or "manual-download"

      // Enrichment fields — optional, written by Step 5
      "enriched_at": "YYYY-MM-DD",
      "summary": "One paragraph (~50 words) describing what the product is and what it does.",
      "specs": {                                    // only keys the manual actually exposes
        "model": "...",
        "warranty": "...",
        "customer_service": "..."
        // model, dimensions, weight, power, battery, warranty, customer_service, serial_location are common keys
        // other keys allowed when the manual exposes them
      },
      "key_features": ["short chip-style strings", "3–6 entries"],
      "troubleshooting": [
        {"question": "Symptom in plain language", "fix": "1–2 sentences.", "page": 14}
      ],
      "full_text": "Verbatim PDF text from pdftotext, used only by the in-page search filter."
    }
  ],
  "artifact_id": "saved-manuals"   // legacy field, ignored
}
```

The `upsert.py` script enforces:
- Required core fields on every write.
- Schema allowlist (any unknown key rejects the write).
- Atomic write (tmp file + rename).
- Filename-keyed merge — fields not in the payload are preserved on existing entries.

---

## Skill contract

### Environment variables

| Variable | Default | Effect |
|---|---|---|
| `CLAUDE_MANUALS_DIR` | `$HOME/Manuals` | Where manuals, the index, and `MANUALS.html` live. Read by all three scripts. |
| `CLAUDE_MANUALS_AUTO_ENRICH` | `true` | When set to `false`, `0`, `no`, or `off`, Step 5 is skipped globally. |

### Trigger contract

The skill's frontmatter `description` is the trigger surface. It fires when the user wants to "save / find / archive / download an instruction manual or user guide for any product," when they mention "toss / throw away a physical manual or booklet," and when they list multiple products with manuals to archive.

### Opt-out phrase contract

Step 5 is also skipped when the user's prompt contains any of (case-insensitive substring match):

- skip enrich / no enrich / don't enrich / without enrich
- no summary / skip summary
- just save / just the file / just the pdf
- minimal / fast / quick
- no details / no metadata

This list lives in SKILL.md and is the authoritative reference.

### Filename convention

- Always lowercase kebab-case
- Always `.pdf` extension
- Examples: `polar-h10-user-manual.pdf`, `sonoff-swv-zigbee-water-valve-manual.pdf`
- Avoid: `manual.pdf`, `H10_Manual.pdf`, or names with spaces

---

## Generated artifacts

Inside the archive directory:

```
${CLAUDE_MANUALS_DIR}/
├── .manuals-index.json     # source of truth
├── MANUALS.html            # generated browser view
└── *.pdf                   # the manuals
```

`MANUALS.html` is a single self-contained file: vanilla JS, no build step, no external dependencies, dark-mode aware via `prefers-color-scheme`. It opens in any browser by double-click and can be emailed or AirDropped as a standalone artifact. The data array is injected at generation time into a `__MANUALS_DATA__` placeholder in `templates/MANUALS.template.html`.

---

## Dependencies

| Dependency | Required? | Why |
|---|---|---|
| Python 3 | Required | The three helper scripts. macOS ships with `python3`; no install needed. |
| Claude Code's Read tool (PDF support) | Required | AI extraction reads the PDF directly in the skill's runtime. |
| Web search (the model's WebSearch tool) | Required | Finding source URLs. |
| `pdftotext` (Poppler) | Optional | Provides the `full_text` field that powers the search filter's PDF-body matching. Install with `brew install poppler`. Without it, `full_text` is omitted; search still matches across summary, specs, troubleshooting, etc. |

---

## Future considerations (explicitly deferred)

These were evaluated during design and held back. Each is reasonable to add later; none is in current scope.

- **Purchase metadata** — date, price, store, serial number, warranty end date. Turns the archive into an asset / warranty registry. Low effort. Deferred until repeat use shows the need.
- **Location-in-home filter** — "Kitchen", "Garage", "Property X". Useful with multiple properties or large homes. Low effort.
- **Consumables / replacement parts** — replacement filters, blades, batteries, ink cartridges per product. Medium effort (AI extraction or manufacturer site scrape).
- **Maintenance schedule integration** — "Descale Epson every 6 months", piped into `/schedule` for real reminders. Medium effort.
- **Document grouping** — bundle manual + receipt + warranty cert + serial-plate photo per product. Low effort.
- **OCR fallback for scanned PDFs** — pull text from scanned manuals so `full_text` works. Medium effort, optional system dependency (Tesseract).
- **Per-archive pagination of `MANUALS.html`** — only relevant past ~500–1000 manuals.

---

## Quality bar

- The skill body is concise enough that the model loads it cleanly on every trigger.
- Scripts handle deterministic operations (mutation, regeneration, text extraction); the skill body handles LLM-judgment operations (search, extraction of structured fields, opt-out recognition).
- Atomic writes for both the index and the HTML.
- Schema enforcement at the script boundary, not in the skill body.
- Graceful degradation when Poppler isn't installed.
- The HTML page renders with `table-layout: fixed` so the column widths don't shift when rows expand or collapse.
