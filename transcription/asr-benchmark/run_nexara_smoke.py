#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

import requests


def main() -> None:
    ap = argparse.ArgumentParser(description="Run Nexara ASR smoke benchmark.")
    ap.add_argument("--audio", type=Path, required=True)
    ap.add_argument("--file-id", default="ru-gs-11")
    ap.add_argument("--noise", default="high")
    ap.add_argument("--response-format", default="verbose_json", choices=["json", "text", "verbose_json", "srt", "vtt"])
    ap.add_argument("--language", default="ru")
    ap.add_argument("--base-url", default="https://api.nexara.ru/api/v1")
    ap.add_argument("--out-dir", type=Path, default=Path(__file__).resolve().parent / "runs")
    args = ap.parse_args()

    key = os.environ.get("NEXARA_API_KEY", "").strip()
    if not key:
        raise SystemExit("NEXARA_API_KEY environment variable is required")

    audio = args.audio.resolve()
    if not audio.is_file():
        raise SystemExit(f"Audio not found: {audio}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"{args.file_id}-nexara-{ts}"
    txt_out = args.out_dir / f"{run_id}.txt"
    json_out = args.out_dir / f"{run_id}.json"

    headers = {"Authorization": f"Bearer {key}"}
    endpoint = f"{args.base_url}/audio/transcriptions"

    with open(audio, "rb") as f:
        files = {"file": (audio.name, f, "audio/wav")}
        data = {
            "response_format": args.response_format,
            "language": args.language,
        }
        t0 = time.time()
        resp = requests.post(endpoint, headers=headers, files=files, data=data, timeout=600)
        t1 = time.time()

    meta = {
        "run_id": run_id,
        "file_id": args.file_id,
        "noise": args.noise,
        "engine": "nexara-transcriptions",
        "audio_path": str(audio),
        "endpoint": endpoint,
        "http_status": resp.status_code,
        "elapsed_sec": round(t1 - t0, 3),
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }

    content_type = resp.headers.get("content-type", "")
    body_obj: dict | str
    text_body = resp.text
    if "application/json" in content_type:
        try:
            body_obj = resp.json()
        except Exception:
            body_obj = {"raw_text": text_body}
    else:
        body_obj = {"raw_text": text_body}

    meta["response_content_type"] = content_type
    if isinstance(body_obj, dict):
        body_obj["_meta"] = meta
        json_out.write_text(json.dumps(body_obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Best-effort transcription text extraction
        transcript_text = ""
        for k in ("text", "transcript", "result"):
            v = body_obj.get(k)
            if isinstance(v, str):
                transcript_text = v
                break
        if not transcript_text and isinstance(body_obj.get("raw_text"), str):
            transcript_text = body_obj["raw_text"]
        txt_out.write_text(transcript_text.strip() + "\n", encoding="utf-8")
        meta["transcript_chars"] = len(transcript_text.strip())
    else:
        json_out.write_text(json.dumps({"raw_text": body_obj, "_meta": meta}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        txt_out.write_text(str(body_obj).strip() + "\n", encoding="utf-8")
        meta["transcript_chars"] = len(str(body_obj).strip())

    print(f"OK run_id={run_id}")
    print(f"status={resp.status_code}")
    print(f"transcript={txt_out}")
    print(f"json={json_out}")
    print(f"chars={meta['transcript_chars']}")


if __name__ == "__main__":
    main()
