#!/usr/bin/env python3
from __future__ import annotations

import argparse
from difflib import SequenceMatcher
import json
import re
import subprocess
import tempfile
import time
from pathlib import Path

from transformers import AutoModel


def normalize_for_dedupe(text: str) -> str:
    t = text.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def dedupe_lines(lines: list[str], min_words: int = 4) -> list[str]:
    out: list[str] = []
    seen_norm: set[str] = set()
    prev_norm = ""
    for line in lines:
        norm = normalize_for_dedupe(line)
        if not norm:
            continue
        if len(norm.split()) < min_words:
            # keep short fragments only if they are not immediate duplicates
            if norm == prev_norm:
                continue
            out.append(line)
            prev_norm = norm
            continue
        if norm == prev_norm:
            continue
        if norm in seen_norm:
            continue
        out.append(line)
        seen_norm.add(norm)
        prev_norm = norm
    return out


def dedupe_lines_strong(
    lines: list[str],
    min_words: int = 4,
    similarity_threshold: float = 0.9,
    keep_global_repeats: int = 1,
) -> list[str]:
    """
    Stronger loop filter for ASR outputs:
    - drops adjacent near-duplicates by normalized similarity
    - limits global repeats of the same normalized phrase
    """
    out: list[str] = []
    prev_norm = ""
    prev_raw = ""
    global_counts: dict[str, int] = {}

    for line in lines:
        norm = normalize_for_dedupe(line)
        if not norm:
            continue

        words = norm.split()
        if len(words) < min_words:
            # still guard against adjacent stutter-like duplicates
            if norm == prev_norm:
                continue
            out.append(line)
            prev_norm = norm
            prev_raw = line
            continue

        # adjacent fuzzy duplicate suppression
        if prev_raw:
            sim = SequenceMatcher(None, line.strip().lower(), prev_raw.strip().lower()).ratio()
            if sim >= similarity_threshold:
                continue

        # global phrase repeat cap
        c = global_counts.get(norm, 0)
        if c >= keep_global_repeats:
            continue
        global_counts[norm] = c + 1

        out.append(line)
        prev_norm = norm
        prev_raw = line

    return out


def ffmpeg_segment(src: Path, out_dir: Path, segment_sec: int) -> list[Path]:
    pattern = out_dir / "seg_%04d.wav"
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(src),
        "-f",
        "segment",
        "-segment_time",
        str(segment_sec),
        "-c",
        "copy",
        str(pattern),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr or proc.stdout or "ffmpeg segment failed")
    return sorted(out_dir.glob("seg_*.wav"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Run GigaAM-v3 chunked transcription without longform API.")
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--file-id", default="ru-gs-11")
    ap.add_argument("--noise", default="high")
    ap.add_argument("--revision", default="e2e_ctc")
    ap.add_argument("--model-id", default="ai-sage/GigaAM-v3")
    ap.add_argument("--segment-sec", type=int, default=45)
    ap.add_argument("--dedupe", action="store_true", help="Apply simple line deduplication post-process.")
    ap.add_argument("--dedupe-strong", action="store_true", help="Apply stronger anti-loop filtering.")
    ap.add_argument("--dedupe-min-words", type=int, default=4, help="Min words to treat line as dedupe candidate.")
    ap.add_argument("--dedupe-similarity", type=float, default=0.9, help="Adjacent fuzzy duplicate threshold (0..1).")
    ap.add_argument("--dedupe-keep-global-repeats", type=int, default=1, help="How many global repeats to keep per normalized phrase.")
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "runs")
    args = ap.parse_args()

    audio = args.audio.resolve()
    if not audio.exists():
        raise SystemExit(f"Audio not found: {audio}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"{args.file_id}-gigaam-{args.revision}-chunked-{ts}"
    txt_out = args.out_dir / f"{run_id}.txt"
    meta_out = args.out_dir / f"{run_id}.json"

    t0 = time.time()
    model = AutoModel.from_pretrained(args.model_id, revision=args.revision, trust_remote_code=True)
    t1 = time.time()

    merged: list[str] = []
    seg_count = 0
    with tempfile.TemporaryDirectory(prefix="gigaam-seg-") as td:
        segs = ffmpeg_segment(audio, Path(td), args.segment_sec)
        seg_count = len(segs)
        for seg in segs:
            txt = model.transcribe(str(seg))
            if isinstance(txt, dict):
                rendered = json.dumps(txt, ensure_ascii=False)
            else:
                rendered = str(txt)
            rendered = rendered.strip()
            if rendered:
                merged.append(rendered)

    if args.dedupe_strong:
        merged_post = dedupe_lines_strong(
            merged,
            min_words=args.dedupe_min_words,
            similarity_threshold=args.dedupe_similarity,
            keep_global_repeats=args.dedupe_keep_global_repeats,
        )
    elif args.dedupe:
        merged_post = dedupe_lines(merged, min_words=args.dedupe_min_words)
    else:
        merged_post = merged
    final_text = "\n".join(merged_post).strip() + "\n"
    txt_out.write_text(final_text, encoding="utf-8")
    t2 = time.time()

    meta = {
        "run_id": run_id,
        "file_id": args.file_id,
        "noise": args.noise,
        "engine": f"gigaam-v3-{args.revision}",
        "mode": "chunked",
        "segment_sec": args.segment_sec,
        "segments_total": seg_count,
        "segments_nonempty": len(merged),
        "segments_after_dedupe": len(merged_post),
        "dedupe_enabled": bool(args.dedupe),
        "dedupe_strong_enabled": bool(args.dedupe_strong),
        "dedupe_min_words": args.dedupe_min_words,
        "dedupe_similarity": args.dedupe_similarity,
        "dedupe_keep_global_repeats": args.dedupe_keep_global_repeats,
        "audio_path": str(audio),
        "model_id": args.model_id,
        "revision": args.revision,
        "model_load_sec": round(t1 - t0, 3),
        "transcribe_sec": round(t2 - t1, 3),
        "transcript_chars": len(final_text.strip()),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    meta_out.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK run_id={run_id}")
    print(f"transcript={txt_out}")
    print(f"meta={meta_out}")
    print(f"chars={meta['transcript_chars']}")


if __name__ == "__main__":
    main()
