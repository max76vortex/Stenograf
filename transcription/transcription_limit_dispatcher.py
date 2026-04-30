#!/usr/bin/env python3
"""
Dispatch Phase A transcription in batches constrained by free-tier limits.

Default profile matches Groq Whisper free limits:
- 20 requests/minute
- 2000 requests/day
- 7200 audio seconds/hour
- 28800 audio seconds/day
- 25 MB max file size
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg", ".opus", ".mp4"}


@dataclass
class Limits:
    requests_per_window: int
    window_seconds: int
    requests_per_day: int
    audio_seconds_per_window: int
    audio_seconds_per_day: int
    max_file_mb: int


def utc_now_ts() -> float:
    return time.time()


def iso_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_audio(input_dir: Path, recursive: bool) -> list[Path]:
    if recursive:
        files = [p for p in input_dir.rglob("*") if p.is_file()]
    else:
        files = [p for p in input_dir.iterdir() if p.is_file()]
    return sorted([p for p in files if p.suffix.lower() in DEFAULT_EXTS])


def load_processed_manifest(manifest: Path) -> set[str]:
    if not manifest.exists():
        return set()
    done: set[str] = set()
    with manifest.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            src = (row.get("mp3_path") or row.get("source_file") or "").strip()
            if src:
                done.add(str(Path(src)))
    return done


def ffprobe_duration_sec(path: Path) -> float | None:
    if not shutil.which("ffprobe"):
        return None
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        return None
    try:
        v = float(proc.stdout.strip())
        if v > 0:
            return v
    except ValueError:
        return None
    return None


def estimate_duration_sec(path: Path, fallback_kbps: int = 96) -> float:
    probed = ffprobe_duration_sec(path)
    if probed is not None:
        return probed
    bits = path.stat().st_size * 8
    return max(1.0, bits / (fallback_kbps * 1000.0))


def load_state(path: Path) -> dict:
    if not path.exists():
        return {
            "window_started_at": utc_now_ts(),
            "window_requests_used": 0,
            "window_audio_seconds_used": 0.0,
            "day_started_at": utc_now_ts(),
            "day_requests_used": 0,
            "day_audio_seconds_used": 0.0,
            "processed_sources": [],
            "last_updated_at": iso_now(),
        }
    state = json.loads(path.read_text(encoding="utf-8"))
    if "processed_sources" not in state or not isinstance(state["processed_sources"], list):
        state["processed_sources"] = []
    return state


def save_state(path: Path, state: dict) -> None:
    state["last_updated_at"] = iso_now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def roll_windows_if_needed(state: dict, limits: Limits, now: float) -> None:
    if now - float(state["window_started_at"]) >= limits.window_seconds:
        state["window_started_at"] = now
        state["window_requests_used"] = 0
        state["window_audio_seconds_used"] = 0.0
    if now - float(state["day_started_at"]) >= 86400:
        state["day_started_at"] = now
        state["day_requests_used"] = 0
        state["day_audio_seconds_used"] = 0.0


def remaining_capacity(state: dict, limits: Limits) -> dict:
    return {
        "window_requests": max(0, limits.requests_per_window - int(state["window_requests_used"])),
        "window_audio_seconds": max(0.0, limits.audio_seconds_per_window - float(state["window_audio_seconds_used"])),
        "day_requests": max(0, limits.requests_per_day - int(state["day_requests_used"])),
        "day_audio_seconds": max(0.0, limits.audio_seconds_per_day - float(state["day_audio_seconds_used"])),
    }


def run_single_file_transcription(
    file_path: Path,
    script_dir: Path,
    output_dir: Path,
    manifest: Path,
    asset_root: Path | None,
    overwrite: bool,
    asr_provider: str,
    model: str,
    language: str,
) -> int:
    with tempfile.TemporaryDirectory(prefix="transcribe-batch-") as td:
        temp_dir = Path(td)
        temp_file = temp_dir / file_path.name
        shutil.copy2(file_path, temp_file)
        py = str(Path(__file__).resolve().parent / ".venv" / "Scripts" / "python.exe")
        if not Path(py).exists():
            py = "python"
        cmd = [
            py,
            str(script_dir / "transcribe_to_obsidian.py"),
            str(temp_dir),
            str(output_dir),
            "--asr-provider",
            asr_provider,
            "--model",
            model,
            "--language",
            language,
            "--manifest",
            str(manifest),
            "--ext",
            file_path.suffix.lower(),
        ]
        if asset_root:
            cmd.extend(["--asset-root", str(asset_root)])
        if overwrite:
            cmd.append("--overwrite")
        print(f"RUN: {subprocess.list2cmdline(cmd)}")
        proc = subprocess.run(cmd, cwd=script_dir)
        return proc.returncode


def main() -> None:
    ap = argparse.ArgumentParser(description="Dispatch transcription jobs under free-tier limits.")
    ap.add_argument("--input-dir", type=Path, required=True, help="Root with source audio files.")
    ap.add_argument("--output-dir", type=Path, required=True, help="Output inbox dir for markdown transcripts.")
    ap.add_argument("--manifest", type=Path, required=True, help="Manifest CSV used by transcribe_to_obsidian.py.")
    ap.add_argument("--asset-root", type=Path, default=None, help="Optional asset root for Phase A asset mode.")
    ap.add_argument("--recursive", action="store_true", help="Search input directory recursively.")
    ap.add_argument("--overwrite", action="store_true", help="Pass --overwrite to transcribe_to_obsidian.py.")
    ap.add_argument("--watch", action="store_true", help="Run continuously and wait for next limit window.")
    ap.add_argument("--state-file", type=Path, default=None, help="Persistent state JSON path.")
    ap.add_argument("--requests-per-window", type=int, default=20)
    ap.add_argument("--window-seconds", type=int, default=60)
    ap.add_argument("--requests-per-day", type=int, default=2000)
    ap.add_argument("--audio-seconds-per-window", type=int, default=7200)
    ap.add_argument("--audio-seconds-per-day", type=int, default=28800)
    ap.add_argument("--max-file-mb", type=int, default=25)
    ap.add_argument("--sleep-poll-seconds", type=int, default=10)
    ap.add_argument("--asr-provider", default="speech2text-transcriptions")
    ap.add_argument("--asr-model", default="whisper-1")
    ap.add_argument("--asr-language", default="ru")
    args = ap.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    manifest = args.manifest.resolve()
    state_file = (args.state_file.resolve() if args.state_file else input_dir / ".transcription_limit_state.json")
    script_dir = Path(__file__).resolve().parent

    limits = Limits(
        requests_per_window=args.requests_per_window,
        window_seconds=args.window_seconds,
        requests_per_day=args.requests_per_day,
        audio_seconds_per_window=args.audio_seconds_per_window,
        audio_seconds_per_day=args.audio_seconds_per_day,
        max_file_mb=args.max_file_mb,
    )

    print(
        "Limits profile: "
        f"{limits.requests_per_window} req/{limits.window_seconds}s, "
        f"{limits.requests_per_day} req/day, "
        f"{limits.audio_seconds_per_window:.0f} audio-sec/window, "
        f"{limits.audio_seconds_per_day:.0f} audio-sec/day, "
        f"max {limits.max_file_mb} MB/file"
    )

    while True:
        all_files = discover_audio(input_dir, recursive=args.recursive)
        done = load_processed_manifest(manifest)
        state = load_state(state_file)
        processed_sources = set(str(Path(p)) for p in state.get("processed_sources", []))
        pending = [p for p in all_files if str(p) not in done and str(p) not in processed_sources]
        if not pending:
            print("Queue empty: no pending files.")
            if not args.watch:
                return
            time.sleep(max(5, args.sleep_poll_seconds))
            continue

        now = utc_now_ts()
        roll_windows_if_needed(state, limits, now)
        cap = remaining_capacity(state, limits)

        if cap["window_requests"] <= 0 or cap["day_requests"] <= 0 or cap["window_audio_seconds"] <= 0 or cap["day_audio_seconds"] <= 0:
            to_window = max(1, int(limits.window_seconds - (now - float(state["window_started_at"]))))
            to_day = max(1, int(86400 - (now - float(state["day_started_at"]))))
            sleep_for = min(to_window, to_day)
            print(f"Limit reached, sleeping {sleep_for}s (next window/day reset).")
            save_state(state_file, state)
            if not args.watch:
                return
            time.sleep(sleep_for)
            continue

        processed_in_cycle = 0
        for src in pending:
            if processed_in_cycle >= cap["window_requests"] or processed_in_cycle >= cap["day_requests"]:
                break

            size_mb = src.stat().st_size / (1024 * 1024)
            if size_mb > limits.max_file_mb:
                print(f"SKIP too large: {src} ({size_mb:.2f} MB > {limits.max_file_mb} MB)")
                continue

            audio_sec = estimate_duration_sec(src)
            if audio_sec > cap["window_audio_seconds"] or audio_sec > cap["day_audio_seconds"]:
                break

            rc = run_single_file_transcription(
                file_path=src,
                script_dir=script_dir,
                output_dir=output_dir,
                manifest=manifest,
                asset_root=args.asset_root.resolve() if args.asset_root else None,
                overwrite=args.overwrite,
                asr_provider=args.asr_provider,
                model=args.asr_model,
                language=args.asr_language,
            )

            state["window_requests_used"] = int(state["window_requests_used"]) + 1
            state["day_requests_used"] = int(state["day_requests_used"]) + 1
            state["window_audio_seconds_used"] = float(state["window_audio_seconds_used"]) + audio_sec
            state["day_audio_seconds_used"] = float(state["day_audio_seconds_used"]) + audio_sec
            save_state(state_file, state)

            if rc != 0:
                raise SystemExit(f"Transcription failed for {src} (exit={rc})")

            state["processed_sources"].append(str(src))
            state["processed_sources"] = state["processed_sources"][-50000:]
            save_state(state_file, state)

            processed_in_cycle += 1
            cap["window_audio_seconds"] -= audio_sec
            cap["day_audio_seconds"] -= audio_sec
            cap["window_requests"] -= 1
            cap["day_requests"] -= 1

        print(
            "Cycle done: "
            f"processed={processed_in_cycle}, "
            f"remaining window req={cap['window_requests']}, day req={cap['day_requests']}, "
            f"window audio sec={cap['window_audio_seconds']:.0f}, day audio sec={cap['day_audio_seconds']:.0f}"
        )

        if not args.watch:
            return
        if processed_in_cycle == 0:
            time.sleep(max(5, args.sleep_poll_seconds))


if __name__ == "__main__":
    main()
