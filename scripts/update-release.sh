#!/usr/bin/env bash
# Create or update the GitHub Release for one channel's transcripts.
# Usage: GH_TOKEN=... ./scripts/update-release.sh <slug>
set -euo pipefail

SLUG="$1"

[ -d "transcripts/$SLUG" ] || { echo "No transcripts dir for $SLUG, skipping."; exit 0; }

zip -r "$SLUG.zip" "transcripts/$SLUG/"
gh release delete "transcripts-$SLUG" --yes 2>/dev/null || true
gh release create "transcripts-$SLUG" "$SLUG.zip" \
  --title "$SLUG transcripts (latest)" \
  --notes "Auto-updated by workflow. Download \`$SLUG.zip\` for all $SLUG transcripts." \
  --latest=false
rm "$SLUG.zip"
