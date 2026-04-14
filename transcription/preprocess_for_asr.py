#!/usr/bin/env python3
"""
Предобработка аудио для ASR (Whisper): ffmpeg — high-pass, шумоподавление,
ресэмпл 16 kHz mono, loudnorm. Выход: *_asr.wav рядом с исходником.

Требуется ffmpeg в PATH (winget: `Gyan.FFmpeg`; если WinGet падает на `P:\temp`, задайте TEMP/TMP на диск C: перед установкой).
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(
        description="ffmpeg: highpass + afftdn + 16 kHz mono + loudnorm -> *_asr.wav"
    )
    ap.add_argument("input", type=Path, help="Входной mp3/wav/m4a")
    ap.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Выходной WAV (по умолчанию: <stem>_asr.wav рядом с входом)",
    )
    ap.add_argument("--ffmpeg", default="ffmpeg", help="Имя или путь к ffmpeg")
    args = ap.parse_args()

    ff = shutil.which(args.ffmpeg) or args.ffmpeg
    inp = args.input.resolve()
    if not inp.is_file():
        raise SystemExit(f"Файл не найден: {inp}")

    out = args.output.resolve() if args.output else inp.with_name(inp.stem + "_asr.wav")

    # Однопроходный loudnorm для речи; лёгкое шумоподавление afftdn
    af = (
        "highpass=f=120,"
        "afftdn=nf=-25,"
        "aresample=16000,"
        "loudnorm=I=-16:TP=-1.5:LRA=11"
    )
    cmd = [
        ff,
        "-hide_banner",
        "-nostats",
        "-y",
        "-i",
        str(inp),
        "-af",
        af,
        "-ac",
        "1",
        "-ar",
        "16000",
        "-c:a",
        "pcm_s16le",
        str(out),
    ]
    print(" ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        sys.stderr.write(r.stderr or r.stdout or "")
        raise SystemExit(f"ffmpeg failed ({r.returncode})")
    print(f"OK -> {out}")


if __name__ == "__main__":
    main()
