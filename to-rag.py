#!/usr/bin/env python3
"""Convert (json3, info.json) pairs into RAG-ready markdown.

For each `<base>.en.json3` + `<base>.info.json` pair in INPUT_DIR, writes
`<base>.md` to OUTPUT_DIR with YAML frontmatter and prose body, with sparse
[mm:ss] timestamps inserted at sentence boundaries roughly every TS_INTERVAL_SEC.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

TS_INTERVAL_SEC = 30

SLIM_FIELDS = (
    "id",
    "title",
    "channel",
    "channel_url",
    "uploader",
    "language",
    "duration_string",
    "view_count",
    "like_count",
    "comment_count",
    "tags",
    "categories",
    "thumbnail",
    "webpage_url",
    "chapters",
)

# Bracketed annotations from auto-captions like [music], [applause], [laughter].
# Matches any [...] containing at least one letter — won't touch our [00:00] markers
# because those are inserted later.
ANNOTATION_RE = re.compile(r"\s*\[[^\]]*[A-Za-z][^\]]*\]\s*")

# Speaker-change markers (>>) from auto-captions. Strip runs of them.
SPEAKER_RE = re.compile(r"\s*>>+\s*")

# Filename normalisation: yt-dlp uses fullwidth replacements for filesystem-unsafe
# chars (？ ＂ ： ＊ ＜ ＞ ｜ ／ ＼). Drop them and collapse whitespace.
FULLWIDTH_DROP = str.maketrans("", "", "？＂：＊＜＞｜／＼")


def clean_filename(name: str) -> str:
    name = name.translate(FULLWIDTH_DROP)
    name = re.sub(r"\s+", " ", name).strip()
    name = re.sub(r"\s*-\s*", " - ", name)
    return name


def fmt_ts(seconds: int) -> str:
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def fmt_upload_date(yyyymmdd: str | None) -> str | None:
    if not yyyymmdd or len(yyyymmdd) != 8 or not yyyymmdd.isdigit():
        return yyyymmdd
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"


def extract_transcript(events: list, ts_interval: int = TS_INTERVAL_SEC) -> str:
    parts: list[str] = ["[00:00] "]
    last_marker = 0

    for ev in events:
        segs = ev.get("segs")
        if not segs or ev.get("aAppend"):
            continue
        text = "".join(s.get("utf8", "") for s in segs)
        text = text.replace("\xa0", " ").replace("\n", " ")
        text = ANNOTATION_RE.sub(" ", text)
        text = SPEAKER_RE.sub(" ", text).strip()
        if not text:
            continue

        t = ev.get("tStartMs", 0) // 1000
        prev = parts[-1].rstrip() if parts else ""
        crossed = t - last_marker >= ts_interval
        sentence_end = prev.endswith((".", "!", "?"))

        if crossed and sentence_end:
            parts.append(f"\n\n[{fmt_ts(t)}] ")
            last_marker = t
        elif parts and not parts[-1].endswith((" ", "\n", "[")):
            parts.append(" ")

        parts.append(text)

    out = "".join(parts).strip()
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out


def yaml_inline(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, list):
        return "[" + ", ".join(yaml_inline(x) for x in v) + "]"
    s = str(v).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def build_frontmatter(info: dict, retrieved_at: str) -> str:
    lines = ["---", f"retrieved_at: {retrieved_at}"]
    upload = fmt_upload_date(info.get("upload_date"))
    if upload:
        lines.append(f"upload_date: {upload}")
    for k in SLIM_FIELDS:
        v = info.get(k)
        if v is None:
            continue
        lines.append(f"{k}: {yaml_inline(v)}")
    lines.append("---")
    return "\n".join(lines)


def process(json3_path: Path, info_path: Path, out_dir: Path, retrieved_at: str) -> Path:
    info = json.loads(info_path.read_text())
    j3 = json.loads(json3_path.read_text())
    transcript = extract_transcript(j3.get("events", []))
    fm = build_frontmatter(info, retrieved_at)
    title = info.get("title", json3_path.stem)
    description = (info.get("description") or "").strip()

    body = f"{fm}\n\n# {title}\n\n{transcript}\n"
    if description:
        body += f"\n---\n\n## Description\n\n{description}\n"

    base = json3_path.name
    if base.endswith(".en.json3"):
        base = base[: -len(".en.json3")]
    else:
        base = json3_path.stem
    base = clean_filename(base)

    out = out_dir / f"{base}.md"
    out.write_text(body)
    return out


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: srt-to-rag.py <input-dir> [output-dir]", file=sys.stderr)
        return 2

    in_dir = Path(sys.argv[1])
    out_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else in_dir / "rag"
    out_dir.mkdir(parents=True, exist_ok=True)
    retrieved_at = date.today().isoformat()

    pairs: list[tuple[Path, Path]] = []
    for j3 in sorted(in_dir.glob("*.en.json3")):
        base = j3.name[: -len(".en.json3")]
        info = in_dir / f"{base}.info.json"
        if info.exists():
            pairs.append((j3, info))

    if not pairs:
        print(f"No (*.en.json3, *.info.json) pairs found in {in_dir}", file=sys.stderr)
        return 1

    print(f"Converting {len(pairs)} videos -> {out_dir}/")
    for j3, info in pairs:
        out = process(j3, info, out_dir, retrieved_at)
        print(f"  {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
