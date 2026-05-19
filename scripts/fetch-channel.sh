#!/usr/bin/env bash
# Fetch and convert transcripts for one channel.
# Usage: ./scripts/fetch-channel.sh <slug> <url> [limit]
set -euo pipefail

SLUG="$1"
URL="$2"
LIMIT="${3:-}"

mkdir -p ".yt-archives" "transcripts/$SLUG" subs

[ -f ".yt-archives/$SLUG.txt" ] && cp ".yt-archives/$SLUG.txt" subs/.downloaded.txt || rm -f subs/.downloaded.txt

CHANNEL="$URL" OUT_DIR=subs ARCHIVE=subs/.downloaded.txt \
  ${LIMIT:+LIMIT=$LIMIT} ./fetch.sh "$URL"

python3 to-rag.py subs "transcripts/$SLUG"

[ -f subs/.downloaded.txt ] && cp subs/.downloaded.txt ".yt-archives/$SLUG.txt"

rm -rf subs
