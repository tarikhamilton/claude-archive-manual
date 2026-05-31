---
name: archive-manual
description: Find official instruction manuals or user guides online, download them to ~/Dropbox/Manuals/, maintain a JSON index, and keep MANUALS.md up to date. Use when the user wants to save, find, archive, or download an instruction manual or user guide for any product — or mentions wanting to toss/throw away a physical manual or booklet. Also triggers when the user lists multiple products with manuals to archive.
---

# Archive Manual

Find official instruction manuals online and save them to ~/Dropbox/Manuals/.

## Destination
~/Dropbox/Manuals/ — create if it doesn't exist.

File naming: kebab-case, always .pdf
Good: polar-h10-user-manual.pdf, sonoff-swv-zigbee-water-valve-manual.pdf
Avoid: manual.pdf, H10_Manual.pdf, names with spaces

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
# Check if already exists first
if [ -s ~/Dropbox/Manuals/filename.pdf ]; then
  echo "Already exists, skipping"
else
  curl -L -o ~/Dropbox/Manuals/filename.pdf "PRIMARY_URL" --max-time 60 -s
  # If that fails, try fallback:
  [ -s ~/Dropbox/Manuals/filename.pdf ] || curl -L -o ~/Dropbox/Manuals/filename.pdf "FALLBACK_URL" --max-time 60 -s
fi
```

Verify the downloaded file is a real PDF (`head -c 4` should return `%PDF`) before considering it successful. HTML error pages frequently come back as 200s.

Status: `downloaded` if curl succeeded AND the file is a real PDF, `manual-download` if no direct PDF exists anywhere.

For `manual-download` cases, tell the user the ManualsLib URL and the exact filename to save as.

---

## Step 3: Update the index

Read `~/Dropbox/Manuals/.manuals-index.json`. Create if missing:

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

## Step 4: Regenerate the summary

After updating the index, write `~/Dropbox/Manuals/MANUALS.md` — a clean markdown table of all manuals.

Format:

```
| Product | File | Source | Saved | Status |
|---------|------|--------|-------|--------|
| Polar H10 Heart Rate Monitor | polar-h10-user-manual.pdf | [Polar Official](url) | 2026-05-21 | ✅ |
| Whirlpool Fridge ET8WTK | whirlpool-...pdf | [ManualsLib](url) | 2026-05-23 | ⬇ manual |
```

Counts at the top: "12 manuals · 11 downloaded · 1 needs manual download"

---

## Finishing up

Keep the response brief:
- One line per product: what you found and where
- Whether it downloaded or needs manual action
- Done — no narrating every step
