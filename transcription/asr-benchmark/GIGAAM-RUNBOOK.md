# GigaAM-v3 smoke runbook (WS-025)

## Purpose

Run a real smoke check of `ai-sage/GigaAM-v3` on a problematic RU asset and write measurable output to benchmark artifacts.

Model page: [ai-sage/GigaAM-v3](https://huggingface.co/ai-sage/GigaAM-v3)

## What this runbook produces

- transcript file under `transcription/asr-benchmark/runs/`
- metadata JSON with timing and environment
- one row for engine `gigaam-v3-e2e_rnnt` in `transcription/asr-benchmark/results.csv` (manual scoring step)

## Environment

Use a dedicated venv to avoid breaking current Phase A environment:

```powershell
cd "c:\Users\sa\N8N-projects\transcription"
python -m venv ".venv-gigaam"
& ".\.venv-gigaam\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv-gigaam\Scripts\python.exe" -m pip install torch==2.8.0 torchaudio==2.8.0 transformers==4.57.1 sentencepiece
```

If install fails on exact versions, keep `transformers` pinned and use nearest compatible `torch/torchaudio` for your CUDA stack.

Additional prerequisites for long files:

- set `HF_TOKEN` environment variable (required by `transcribe_longform` segmentation in model runtime),
- ensure `torchcodec` works with installed FFmpeg and torch build.
- GPU recommended: verify `torch==2.8.0+cu128` and `torch.cuda.is_available()==True` in `.venv-gigaam`.

## Smoke run command

```powershell
& "c:\Users\sa\N8N-projects\transcription\.venv-gigaam\Scripts\python.exe" `
  "c:\Users\sa\N8N-projects\transcription\asr-benchmark\run_gigaam_smoke.py" `
  --audio "D:\1 ЗАПИСИ ГОЛОС\audio-work\2005-01\2005-01-01_002_2005-11-15_002_DW_C0143__src-20050101\2005-11-15_002_DW_C0143_asr.wav" `
  --file-id "ru-gs-11" `
  --noise "high" `
  --revision "e2e_rnnt"
```

## Manual scoring (required)

After run completes:

1. Open transcript in `transcription/asr-benchmark/runs/`.
2. Score the row using WS-025 gate fields:
   - `A_loops`, `A_empty`, `A_coherence`, `A_pass`
   - `post_edit_min_per_10`, `punctuation_1_5`, `terms_1_5`
3. Append/update row in `results.csv` with engine `gigaam-v3-e2e_rnnt`.

## Acceptance check for this smoke

- Script exits with code 0.
- Transcript is non-empty.
- Runtime metrics recorded in JSON.
- `results.csv` includes at least one real (non-simulated) row for GigaAM.

If transcript is empty or longform fails:

- record the run as real-smoke fail in `results.csv`,
- capture blockers in `decision.md`,
- do not promote GigaAM to primary/fallback until environment is fixed and rerun passes.

If longform is unavailable (no token), run tokenless fallback:

```powershell
& ".\.venv-gigaam\Scripts\python.exe" ".\asr-benchmark\run_gigaam_chunked.py" `
  --audio "<path_to_wav>" --file-id "<id>" --noise "high" --revision "e2e_ctc" `
  --segment-sec 6 --dedupe --dedupe-min-words 4
```
