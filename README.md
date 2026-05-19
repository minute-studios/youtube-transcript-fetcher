# youtube-transcript-fetcher

Two small scripts for pulling auto-captioned transcripts from a YouTube channel and turning them into RAG-ready markdown.

## What it does

1. **`fetch.sh`** — downloads English auto-caption transcripts (`.en.json3`) and metadata (`.info.json`) for every video on a channel via `yt-dlp`. Polite to YouTube (throttled requests, exponential backoff) and resumable (a download archive lets you re-run safely).
2. **`to-rag.py`** — converts each `(json3, info.json)` pair into a single markdown file: slim YAML frontmatter, prose transcript with sparse `[mm:ss]` timestamps at sentence boundaries, and the YouTube description as a separate section.

Output is one `.md` per video, designed to chunk well for retrieval (transcript first, supplementary description after a horizontal rule).

## Requirements

- [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) — `brew install yt-dlp`
- Python 3.10+ (stdlib only, no deps)

## Usage

Defaults to MinuteEarth; pass any channel URL to override.

```bash
# Download all transcripts (resumable; safe to ctrl-C and restart)
./fetch.sh                                              # MinuteEarth -> ./subs
./fetch.sh https://www.youtube.com/@SomeChannel/videos  # custom channel
LIMIT=5 ./fetch.sh                                      # just the latest 5 (testing)
OUT_DIR=./my-subs ./fetch.sh                            # custom output dir

# Convert to RAG markdown
python3 to-rag.py ./subs                                # writes ./subs/rag/*.md
python3 to-rag.py ./subs ./out                          # custom output dir
```

## Output format

```markdown
---
retrieved_at: 2026-05-09
upload_date: 2026-04-30
id: "Jd6elWlKG-g"
title: "Why Don't Blue Whales Eat Fish?"
channel: "MinuteEarth"
duration_string: "2:29"
view_count: 267865
tags: ["krill", "blue whale", ...]
webpage_url: "https://www.youtube.com/watch?v=Jd6elWlKG-g"
---

# Why Don't Blue Whales Eat Fish?

[00:00] The most massive land animals in the world all eat little stuff...

[01:23] But what about the ocean? Like their counterparts on land...

---

## Description

[YouTube description with credits, links, references]
```

`retrieved_at` is the date the metadata snapshot was taken (point-in-time fields like `view_count` should be read against this date, not `upload_date`).

## Notes

- Transcripts are YouTube auto-captions, not human-edited — expect transcription errors.
- `[music]`, `[applause]`, and similar caption annotations are stripped, as are `>>` speaker-change markers.
- Timestamp markers appear roughly every 30s, but only at sentence boundaries, so spacing is uneven.
- The `--download-archive` file (`.downloaded.txt` in the output dir) tracks completed video IDs. Delete it to re-download everything.
