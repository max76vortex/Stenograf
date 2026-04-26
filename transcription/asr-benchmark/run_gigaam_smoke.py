#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
from transformers import AutoModel


def main() -> None:
    ap = argparse.ArgumentParser(description="Run GigaAM-v3 smoke transcription for WS-025.")
    ap.add_argument("--audio", type=Path, required=True, help="Path to source audio file.")
    ap.add_argument("--file-id", default="ru-gs-11", help="Benchmark file id.")
    ap.add_argument("--noise", default="high", help="Noise label (low|med|high).")
    ap.add_argument("--revision", default="e2e_rnnt", help="GigaAM revision.")
    ap.add_argument("--model-id", default="ai-sage/GigaAM-v3", help="HF model id.")
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "runs",
        help="Output directory for transcript and metadata.",
    )
    args = ap.parse_args()

    audio = args.audio.resolve()
    if not audio.is_file():
        raise SystemExit(f"Audio not found: {audio}")

    out_dir = args.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    ts = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"{args.file_id}-gigaam-{args.revision}-{ts}"
    txt_out = out_dir / f"{run_id}.txt"
    meta_out = out_dir / f"{run_id}.json"

    t0 = time.time()
    model = AutoModel.from_pretrained(
        args.model_id,
        revision=args.revision,
        trust_remote_code=True,
    )
    t1 = time.time()
    try:
        text = model.transcribe(str(audio))
    except ValueError as exc:
        # GigaAM v3 raises this for long files; use the documented longform path.
        if "transcribe_longform" in str(exc):
            text = model.transcribe_longform(str(audio))
        else:
            raise
    t2 = time.time()

    if isinstance(text, dict):
        rendered = json.dumps(text, ensure_ascii=False, indent=2)
    else:
        rendered = str(text)

    txt_out.write_text(rendered.strip() + "\n", encoding="utf-8")

    meta = {
        "run_id": run_id,
        "file_id": args.file_id,
        "noise": args.noise,
        "engine": f"gigaam-v3-{args.revision}",
        "audio_path": str(audio),
        "model_id": args.model_id,
        "revision": args.revision,
        "device_cuda_available": bool(torch.cuda.is_available()),
        "model_load_sec": round(t1 - t0, 3),
        "transcribe_sec": round(t2 - t1, 3),
        "transcript_chars": len(rendered.strip()),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    meta_out.write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"OK run_id={run_id}")
    print(f"transcript={txt_out}")
    print(f"meta={meta_out}")
    print(f"chars={meta['transcript_chars']}")


if __name__ == "__main__":
    main()
