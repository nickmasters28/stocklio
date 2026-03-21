#!/usr/bin/env bash
# Called by Claude Code PostToolUse hook after Write operations.
# Generates an OG image for any new .html file written to www/.
set -euo pipefail

FILE=$(jq -r '.tool_input.file_path // ""')

# Only act on .html files inside the www/ directory
case "$FILE" in
  *.html)
    cd /Users/nickmasters/Desktop/stock-ta
    python3 generate_og_images.py "$FILE"
    ;;
esac
