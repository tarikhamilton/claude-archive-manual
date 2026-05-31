#!/bin/bash
# Extract plain text from a PDF using pdftotext (Poppler).
#
# Usage: extract-text.sh <pdf-filename-or-path>
#
# A bare filename (no slash) is resolved against $CLAUDE_MANUALS_DIR
# (default ~/Manuals). An absolute or relative path with a slash is used
# as-is.
#
# Outputs the extracted text on stdout, collapsing whitespace runs.
# Exits 1 with a hint on stderr if pdftotext isn't installed.

set -e

if [ -z "$1" ]; then
  echo "Usage: $(basename "$0") <pdf-filename-or-path>" >&2
  exit 2
fi

if ! command -v pdftotext >/dev/null 2>&1; then
  echo "pdftotext not installed. Install with: brew install poppler" >&2
  exit 1
fi

DIR="${CLAUDE_MANUALS_DIR:-$HOME/Manuals}"
case "$1" in
  */*) FILE="$1" ;;
  *)   FILE="$DIR/$1" ;;
esac

if [ ! -s "$FILE" ]; then
  echo "Not found or empty: $FILE" >&2
  exit 1
fi

# sed collapses runs of 4+ dots (PDF table-of-contents "dot leaders") into a single space.
# 4+ avoids damaging legitimate ellipses (...).
# tr then collapses any whitespace runs introduced by the dot replacement.
pdftotext -layout "$FILE" - 2>/dev/null | sed 's/\.\{4,\}/ /g' | tr -s '[:space:]' ' '
