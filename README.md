# youtube-transcript-fetcher

Two small scripts for pulling auto-captioned transcripts from a YouTube channel and turning them into RAG-ready markdown. A GitHub Actions workflow runs weekly to accumulate new transcripts automatically.

## What it does

1. **`fetch.sh`** — downloads English auto-caption transcripts (`.en.json3`) and metadata (`.info.json`) for every video on a channel via `yt-dlp`. Polite to YouTube (throttled requests, exponential backoff) and resumable (a download archive lets you re-run safely).
2. **`to-rag.py`** — converts each `(json3, info.json)` pair into a single markdown file: slim YAML frontmatter, prose transcript with sparse `[mm:ss]` timestamps at sentence boundaries, and the YouTube description as a separate section.

Output is one `.md` per video, designed to chunk well for retrieval (transcript first, supplementary description after a horizontal rule).

## Accumulated transcripts

Transcripts are committed to this repo under `transcripts/{channel}/` and kept up to date by a weekly workflow. Download a zip of all transcripts for a channel from its GitHub Release:

- **MinuteEarth** — `releases/download/transcripts-minuteearth/minuteearth.zip`

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

## Workflow

The GitHub Actions workflow (`.github/workflows/fetch-transcripts.yml`) runs every Monday at 3am UTC and can also be triggered manually from the Actions tab.

Each channel in the workflow matrix runs as a separate job (in series to avoid conflicts). The workflow:

1. Restores the per-channel download archive from `.yt-archives/{slug}.txt`
2. Downloads only new videos via `scripts/fetch-channel.sh`
3. Converts them to markdown and commits to `transcripts/{slug}/`
4. Publishes an updated zip to the channel's GitHub Release

**Adding a channel** — add one entry to the `matrix.include` in the workflow YAML:

```yaml
- slug: some-channel
  url: https://www.youtube.com/@SomeChannel/videos
```

**Running a single channel manually** — trigger the workflow from the Actions tab, set the `slug` input to the channel's slug (e.g. `minuteearth`). Optionally set `limit` to cap the number of videos fetched (useful for testing).

The scripts under `scripts/` can also be run locally:

```bash
./scripts/fetch-channel.sh minuteearth https://www.youtube.com/@MinuteEarth/videos 5
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
