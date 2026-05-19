#!/usr/bin/env bash
# Commit and push any new transcripts for one channel.
# Usage: ./scripts/commit-changes.sh <slug>
# Sets GITHUB_OUTPUT changed=true/false when running in CI.
set -euo pipefail

SLUG="$1"

git config user.name "github-actions[bot]"
git config user.email "github-actions[bot]@users.noreply.github.com"
git add "transcripts/$SLUG" ".yt-archives/$SLUG.txt"

if git diff --cached --quiet; then
  echo "No new transcripts for $SLUG"
  echo "changed=false" >> "${GITHUB_OUTPUT:-/dev/null}"
  exit 0
fi

COUNT=$(git diff --cached --name-only -- "transcripts/$SLUG" | wc -l | tr -d ' ')
git commit -m "chore: add ${COUNT} $SLUG transcript(s) [skip ci]"
git pull --rebase origin main
git push origin main
echo "changed=true" >> "${GITHUB_OUTPUT:-/dev/null}"
