# GPU: Ollama и LM Studio (архив)

> Архивный документ. В проекте `N8N-projects` рабочий Phase B выполняется только через skill
> `.cursor/skills/phase-b-process/SKILL.md` (Kimi в Cursor). Этот файл сохранён только как исторочная заметка.

## Проверить, использует ли Ollama видеопамять

1. Драйвер NVIDIA: `nvidia-smi` — должна быть видна видеокарта.
2. После любого запроса к модели:
   ```powershell
   curl -s http://127.0.0.1:11434/api/ps
   ```
   В JSON смотри поле **`size_vram`** у загруженной модели.
   - **`size_vram` > 0** — часть весов в VRAM (GPU участвует).
   - **`size_vram`: 0** — модель считается на CPU (часто из‑за нехватки VRAM под выбранный размер/квант).

На **6 GB VRAM** (например RTX 3060 Laptop) модель **~9–10B в Q4** может **не помещаться** целиком в GPU — Ollama уходит на RAM/CPU, в `api/ps` будет **`size_vram: 0`**. Это не «сломанный GPU», а нехватка памяти под модель.

Что можно сделать:

- Взять **меньшую** модель или **сильнее сжатый** квант (например Q3 / меньший контекст в настройках Ollama, если доступно).
- Явно задать число слоёв на GPU только если Ollama это принимает: `--ollama-num-gpu N` (подбирать экспериментально; **не** использовать огромные значения вроде 999).

## LM Studio (локально, свой контроль над GPU)

1. Установи [LM Studio](https://lmstudio.ai/), скачай модель под **свою VRAM** (для 6 GB — обычно **7B и меньше** или сильный квант).
2. Вкладка **GPU**: выставь **число слоёв на GPU** так, чтобы укладывалось в память (ползунок / `n_gpu_layers`).
3. Включи **Local Server** (часто порт **1234**).
4. Имя модели в API — как в списке загруженных (скопируй из UI).
5. Phase B:

```powershell
cd transcription
.\.venv\Scripts\python.exe phase_b_processor.py "D:\1 ЗАПИСИ ГОЛОС\audio-work" `
  --recursive --vault-dir "D:\Obsidian\Audio Brain" `
  --backend openai --openai-base-url "http://127.0.0.1:1234/v1" `
  --model "ИМЯ_МОДЕЛИ_ИЗ_LM_STUDIO" `
  --overwrite --timeout-sec 1800
```

В `meta.json` будет **`llm_backend": "openai"`** и **`openai_base_url`**.

## Скрипт `phase_b_processor.py`

- **`--backend ollama`** (по умолчанию) — Ollama, ответы с полем `thinking` у qwen3.5 учтены в коде.
- **`--backend openai`** — OpenAI-совместимый `/v1/chat/completions` (LM Studio и аналоги).
