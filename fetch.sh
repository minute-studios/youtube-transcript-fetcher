#!/usr/bin/env bash
# Download English subtitles for every video on a YouTube channel.
# Defaults to MinuteEarth. Polite to YouTube via yt-dlp's built-in `sleep` preset:
# --sleep-subtitles 5 --sleep-requests 0.75 --sleep-interval 10 --max-sleep-interval 20
#
# Resumable: --download-archive tracks completed video IDs, so re-running skips them.
# Safe to ctrl-C and restart.
#
# Usage:
#   ./fetch.sh                       # MinuteEarth, ./subs
#   ./fetch.sh <channel-url>         # custom channel
#   OUT_DIR=/path ./fetch.sh         # custom output dir

set -euo pipefail

CHANNEL="${1:-https://www.youtube.com/@MinuteEarth/videos}"
OUT_DIR="${OUT_DIR:-./subs}"
ARCHIVE="${ARCHIVE:-$OUT_DIR/.downloaded.txt}"
LIMIT="${LIMIT:-}"   # set to a number to cap the run (e.g. LIMIT=3 for testing)

if ! command -v yt-dlp >/dev/null 2>&1; then
  echo "yt-dlp not found. Install with: brew install yt-dlp" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

echo "Channel:  $CHANNEL"
echo "Output:   $OUT_DIR"
echo "Archive:  $ARCHIVE"
echo

yt-dlp \
  -t sleep \
  --skip-download \
  --write-auto-subs \
  --sub-langs "en" \
  --sub-format json3 \
  --write-info-json \
  --download-archive "$ARCHIVE" \
  --retries 10 \
  --extractor-retries 5 \
  --retry-sleep "exp=1:60" \
  --ignore-errors \
  --no-overwrites \
  ${LIMIT:+--playlist-end "$LIMIT"} \
  -o "$OUT_DIR/%(upload_date)s - %(title)s.%(ext)s" \
  "$CHANNEL"

echo
echo "Done. Subtitles in: $OUT_DIR"
