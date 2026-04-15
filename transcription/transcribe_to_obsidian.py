#!/usr/bin/env python3
"""
Транскрибация mp3 в .md для Obsidian vault (00_inbox).

Бэкенды:
  --backend local   faster-whisper (GPU/CPU, модель large-v3). По умолчанию.
  --backend groq    Groq Cloud Whisper API (whisper-large-v3-turbo).
  --backend openai  OpenAI Whisper / GPT-4o-transcribe API.

Для cloud-бэкендов нужен --api-key (или переменные GROQ_API_KEY / OPENAI_API_KEY).
"""
import io
import os
import sys
import sysconfig
import urllib.error
import urllib.request
from pathlib import Path
import argparse
import json
import re
import shutil
import time
from datetime import datetime

_GROQ_BASE = "https://api.groq.com/openai/v1"
_OPENAI_BASE = "https://api.openai.com/v1"
_CLOUD_FILE_LIMIT_MB = 25


def _prepend_nvidia_cublas_bin() -> None:
    """Windows: ctranslate2 ищет cublas64_12.dll; pip-пакет nvidia-cublas-cu12 кладёт DLL в site-packages."""
    if sys.platform != "win32":
        return
    try:
        purelib = Path(sysconfig.get_paths()["purelib"])
        bin_dir = purelib / "nvidia" / "cublas" / "bin"
        if (bin_dir / "cublas64_12.dll").is_file():
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


def _load_whisper_model(model: str, device: str, compute_type: str):
    """Lazy import faster-whisper only when backend=local."""
    _prepend_nvidia_cublas_bin()
    from faster_whisper import WhisperModel
    return WhisperModel(model, device=device, compute_type=compute_type)


# ---------------------------------------------------------------------------
# Cloud ASR helpers (Groq / OpenAI compatible)
# ---------------------------------------------------------------------------

def _build_multipart(fields: dict[str, str], file_field: str, file_path: Path) -> tuple[bytes, str]:
    """Build multipart/form-data body from string fields + one file field.

    Returns (body_bytes, content_type_header).
    """
    boundary = f"----PythonFormBoundary{os.urandom(8).hex()}"
    parts: list[bytes] = []
    for key, value in fields.items():
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="{key}"\r\n\r\n'
            f"{value}\r\n".encode()
        )
    file_data = file_path.read_bytes()
    parts.append(
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="{file_field}"; filename="{file_path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n".encode()
        + file_data
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    content_type = f"multipart/form-data; boundary={boundary}"
    return body, content_type


def _cloud_transcribe(
    audio_path: Path,
    *,
    api_base: str,
    api_key: str,
    model: str,
    language: str | None,
    prompt: str,
    response_format: str = "json",
    timeout_sec: int = 300,
) -> str:
    """Call OpenAI-compatible /v1/audio/transcriptions (Groq, OpenAI, etc.)."""
    size_mb = audio_path.stat().st_size / (1024 * 1024)
    if size_mb > _CLOUD_FILE_LIMIT_MB:
        raise RuntimeError(
            f"Файл {audio_path.name} ({size_mb:.1f} MB) превышает лимит API ({_CLOUD_FILE_LIMIT_MB} MB). "
            f"Сконвертируйте в меньший формат или обрежьте."
        )

    fields: dict[str, str] = {
        "model": model,
        "response_format": response_format,
    }
    if language and language != "auto":
        fields["language"] = language
    if prompt:
        fields["prompt"] = prompt

    body, content_type = _build_multipart(fields, "file", audio_path)
    url = api_base.rstrip("/") + "/audio/transcriptions"

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": content_type,
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "transcribe-to-obsidian/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(f"Cloud ASR HTTP {exc.code}: {err_body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Cloud ASR request failed: {exc}") from exc

    if response_format == "text":
        return raw.strip()
    data = json.loads(raw)
    return (data.get("text") or "").strip()


def slug(s: str) -> str:
    """Безопасное имя файла из строки."""
    s = s.strip()
    s = re.sub(r"[^\w\s\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-") or "transcript"
    return s[:120]


def date_from_path(p: Path) -> str:
    """Пытается извлечь дату из имени файла (YYYY-MM-DD или YYYYMMDD), иначе — дата изменения файла."""
    name = p.stem
    # 2024-03-15 или 20240315
    # День: сначала двузначные варианты, иначе "30" даёт группу "3" (баг с 0?[1-9]).
    m = re.search(r"(20\d{2})[-]?(0?[1-9]|1[0-2])[-]?([12]\d|3[01]|0?[1-9])", name)
    if m:
        y, mon, d = m.groups()
        return f"{y}-{mon.zfill(2)}-{d.zfill(2)}"
    try:
        return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now().strftime("%Y-%m-%d")


def extract_seq_from_name(p: Path) -> str:
    """Извлекает NNN из имени (YYYY-MM-DD_NNN...), иначе 000."""
    m = re.search(r"(?:^|_)(\d{3})(?:_|$)", p.stem)
    return m.group(1) if m else "000"


def src_date_compact_from_path(p: Path) -> str:
    """Дата источника в формате YYYYMMDD: из имени, иначе mtime, иначе today."""
    return date_from_path(p).replace("-", "")


def build_asset_dir_name(audio_path: Path) -> str:
    """YYYY-MM-DD_NNN_slug__src-YYYYMMDD"""
    primary_date = date_from_path(audio_path)
    seq = extract_seq_from_name(audio_path)
    base = slug(audio_path.stem)
    src_date = src_date_compact_from_path(audio_path)
    return f"{primary_date}_{seq}_{base}__src-{src_date}"


def update_meta_json(
    meta_path: Path,
    *,
    asset_dir: Path,
    source_audio_name: str,
    source_audio_path: Path,
    transcript_file: str,
    published_inbox_path: Path | None,
    phase: str,
    asr_input_path: Path | None = None,
) -> None:
    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    data: dict = {}
    if meta_path.exists():
        try:
            loaded = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data = loaded
        except Exception:
            data = {}
    versions = data.get("versions")
    if not isinstance(versions, list):
        versions = []
    ver: dict = {
        "timestamp": now_iso,
        "phase": phase,
        "transcript_file": transcript_file,
        "published_inbox_path": str(published_inbox_path) if published_inbox_path else "",
    }
    if asr_input_path is not None and asr_input_path.resolve() != source_audio_path.resolve():
        ver["asr_input"] = str(asr_input_path.resolve())
    versions.append(ver)
    data.update(
        {
            "phase": phase,
            "audio_file": source_audio_name,
            "source_audio_path": str(source_audio_path),
            "asset_path": str(asset_dir),
            "updated_at": now_iso,
            "versions": versions,
        }
    )
    if "created_at" not in data:
        data["created_at"] = now_iso
    meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_md(audio_path: Path, text: str, date: str, title: str | None, asset_path: Path | None = None) -> str:
    """Собирает .md с frontmatter под шаблон транскрипта Obsidian."""
    audio_name = audio_path.name
    asset_line = f'asset_path: "{asset_path}"\n' if asset_path else ""
    yaml = f"""---
type: transcript
source: audio
audio_file: "{audio_name}"
{asset_line}phase: A
date: "{date}"
status: inbox
tags: [диктофон]
links: []
---

## Заголовок
{title or slug(audio_path.stem)}

## Краткое резюме (заполнить после просмотра)
- **Основные темы**:
- **Ключевые идеи**:
- **Направления**: статьи / проекты / задачи / личное

## Транскрипт

{text}
"""
    return yaml


def _resolve_api_key(args) -> str:
    """Resolve API key from --api-key flag or environment variables."""
    if args.api_key:
        return args.api_key
    env_map = {"groq": "GROQ_API_KEY", "openai": "OPENAI_API_KEY"}
    env_var = env_map.get(args.backend, "")
    key = os.environ.get(env_var, "")
    if not key:
        raise SystemExit(
            f"Для --backend {args.backend} нужен API-ключ: "
            f"передайте --api-key KEY или установите переменную {env_var}"
        )
    return key


def _default_cloud_model(backend: str) -> str:
    if backend == "groq":
        return "whisper-large-v3"
    return "whisper-1"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Transcribe audio files to Markdown for Obsidian 00_inbox."
    )
    ap.add_argument("input_dir", type=Path, help="Папка с .mp3 (или корень с подпапками при --recursive)")
    ap.add_argument("output_dir", type=Path, help="Папка для .md (например vault/00_inbox)")

    # --- Backend selection ---
    ap.add_argument(
        "--backend",
        default="local",
        choices=("local", "groq", "openai"),
        help="ASR-бэкенд: local (faster-whisper, default), groq (Groq Cloud), openai (OpenAI API)",
    )
    ap.add_argument(
        "--api-key",
        default="",
        help="API-ключ для cloud-бэкенда (или переменные GROQ_API_KEY / OPENAI_API_KEY)",
    )
    ap.add_argument(
        "--api-base-url",
        default="",
        help="Базовый URL cloud API (по умолчанию: стандартный для выбранного бэкенда)",
    )
    ap.add_argument(
        "--api-timeout",
        type=int,
        default=300,
        help="Таймаут HTTP-запроса к cloud API в секундах (default: 300)",
    )

    # --- Model & local device ---
    ap.add_argument("--model", default="", help="Модель ASR (default: large-v3 для local, whisper-large-v3 для groq, whisper-1 для openai)")
    ap.add_argument("--device", default="cuda", choices=("cuda", "cpu"), help="Устройство для local-бэкенда")
    ap.add_argument("--compute-type", default="float16", help="float16 для 6GB VRAM (только local)")
    ap.add_argument("--language", default="ru", help="Язык (ru, auto, ...)")
    ap.add_argument("--overwrite", action="store_true", help="Перезаписывать существующие .md")
    ap.add_argument("--recursive", action="store_true", help="Обходить подпапки (recordings/2024-01, 2024-02, ...)")
    ap.add_argument("--manifest", type=Path, default=None, metavar="FILE", help="Лог обработанных: CSV (timestamp, mp3_path, md_name, date)")
    ap.add_argument(
        "--sleep-between-seconds",
        type=float,
        default=0.0,
        metavar="SEC",
        help="Пауза после каждого успешно обработанного файла (снижение нагрузки на GPU/диск; 0 = без паузы)",
    )
    ap.add_argument("--ext", default=".mp3", help="Расширение файлов (default: .mp3)")
    ap.add_argument(
        "--asset-root",
        type=Path,
        default=None,
        metavar="DIR",
        help="Корень asset-папок (новый режим Phase A: перенос исходника + 01_transcript__inbox.md)",
    )
    ap.add_argument(
        "--move-source",
        action="store_true",
        help="Переносить исходный файл в asset-папку (по умолчанию включено в режиме --asset-root)",
    )
    ap.add_argument(
        "--copy-source",
        action="store_true",
        help="Копировать исходный файл в asset-папку (вместо переноса).",
    )
    ap.add_argument(
        "--no-publish-inbox",
        action="store_true",
        help="В режиме --asset-root не публиковать transcript в output_dir (00_inbox).",
    )
    ap.add_argument("--beam-size", type=int, default=5, help="Beam size for decoding (только local, default: 5)")
    ap.add_argument("--best-of", type=int, default=5, help="Best-of candidates (только local, default: 5)")
    ap.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature (default: 0.0)")
    ap.add_argument("--vad-filter", action="store_true", help="Use VAD filtering before decoding (только local)")
    ap.add_argument("--initial-prompt", default="", help="Prompt/контекст для модели (local и cloud)")
    ap.add_argument(
        "--min-text-chars-retry",
        type=int,
        default=0,
        metavar="N",
        help="If transcript shorter than N chars, retry once with language=auto and VAD off (только local)",
    )
    ap.add_argument(
        "--existing-asset",
        action="store_true",
        help="input_dir — уже существующая папка ассета: пишет 01_transcript__inbox.md + inbox; без копирования/переноса",
    )
    ap.add_argument(
        "--preset",
        choices=("quality",),
        default=None,
        help="Пресет параметров. quality: --vad-filter --language auto "
             '--initial-prompt "..." --min-text-chars-retry 50 (если не заданы явно)',
    )
    args = ap.parse_args()

    if args.preset == "quality":
        if not args.vad_filter:
            args.vad_filter = True
        if args.language == "ru":
            args.language = "auto"
        if not args.initial_prompt:
            args.initial_prompt = "Это запись мыслей и идей на русском языке."
        if args.min_text_chars_retry == 0:
            args.min_text_chars_retry = 50
        print(f"[preset=quality] vad_filter=True, language={args.language}, "
              f"min_text_chars_retry={args.min_text_chars_retry}")

    use_cloud = args.backend in ("groq", "openai")

    if args.existing_asset and args.asset_root:
        raise SystemExit("Нельзя использовать одновременно --existing-asset и --asset-root")
    if args.existing_asset and args.recursive:
        raise SystemExit("Нельзя использовать одновременно --existing-asset и --recursive")

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Не найдена папка: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.existing_asset:
        cand = sorted(input_dir.glob(f"*{args.ext}"))
        preferred = [p for p in cand if "_asr" in p.stem.lower()]
        pick = preferred if preferred else cand
        if not pick:
            raise SystemExit(f"Нет файлов *{args.ext} в {input_dir}")
        audio_files = [pick[0]]

        def out_name_for(p: Path) -> str:
            return slug(p.stem) + ".md"
    elif args.recursive:
        audio_files = sorted(input_dir.rglob(f"*{args.ext}"))
        # Имена .md при рекурсии: относительный путь без расширения как slug (избегаем коллизий между папками)
        def out_name_for(p: Path) -> str:
            rel = p.relative_to(input_dir)
            stem = rel.with_suffix("").as_posix().replace("/", "_")
            return slug(stem) + ".md"
    else:
        audio_files = sorted(input_dir.glob(f"*{args.ext}"))
        def out_name_for(p: Path) -> str:
            return slug(p.stem) + ".md"
    if not audio_files:
        print(f"Нет файлов *{args.ext} в {input_dir}")
        return

    asset_root = args.asset_root.resolve() if args.asset_root else None
    publish_inbox = not args.no_publish_inbox
    if asset_root:
        asset_root.mkdir(parents=True, exist_ok=True)
    if args.copy_source and args.move_source:
        raise SystemExit("Нельзя использовать одновременно --copy-source и --move-source")

    # --- Resolve model name and load / validate ---
    effective_model = args.model or ("large-v3" if not use_cloud else _default_cloud_model(args.backend))

    cloud_api_key = ""
    cloud_api_base = ""
    whisper_model = None

    if use_cloud:
        cloud_api_key = _resolve_api_key(args)
        cloud_api_base = args.api_base_url or (_GROQ_BASE if args.backend == "groq" else _OPENAI_BASE)
        print(f"Cloud ASR: backend={args.backend}, model={effective_model}, base={cloud_api_base}")
    else:
        print(f"Загрузка модели {effective_model} ({args.device}, {args.compute_type})...")
        whisper_model = _load_whisper_model(effective_model, args.device, args.compute_type)

    print(f"Обработка {len(audio_files)} файлов -> {output_dir}")

    manifest_file = None
    if args.manifest:
        manifest_file = args.manifest.resolve()
        if not manifest_file.exists():
            if asset_root or args.existing_asset:
                manifest_file.write_text(
                    "timestamp,mp3_path,asset_dir,transcript_file,inbox_md,date,source_action\n",
                    encoding="utf-8",
                )
            else:
                manifest_file.write_text("timestamp,mp3_path,md_name,date\n", encoding="utf-8")

    for i, audio_path in enumerate(audio_files, 1):
        meta: dict = {}
        date = date_from_path(audio_path)
        out_name = out_name_for(audio_path)
        out_path = output_dir / out_name
        source_action = "none"
        source_audio_for_model = audio_path
        transcript_path: Path | None = None
        asset_dir: Path | None = None

        if args.existing_asset:
            asset_dir = input_dir
            transcript_path = asset_dir / "01_transcript__inbox.md"
            source_action = "existing-asset"
            meta_path = asset_dir / "meta.json"
            if meta_path.exists():
                try:
                    loaded = json.loads(meta_path.read_text(encoding="utf-8"))
                    if isinstance(loaded, dict):
                        meta = loaded
                except Exception:
                    meta = {}
            if meta.get("audio_file"):
                out_name = slug(Path(str(meta["audio_file"])).stem) + ".md"
                out_path = output_dir / out_name
                if meta.get("source_audio_path"):
                    try:
                        date = date_from_path(Path(str(meta["source_audio_path"])))
                    except OSError:
                        date = date_from_path(audio_path)
            if transcript_path.exists() and not args.overwrite:
                print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {transcript_path.name}")
                continue
        elif asset_root:
            asset_name = build_asset_dir_name(audio_path)
            asset_month_dir = asset_root / date[:7]
            asset_dir = asset_month_dir / asset_name
            asset_dir.mkdir(parents=True, exist_ok=True)

            target_audio = asset_dir / audio_path.name
            if audio_path.resolve() != target_audio.resolve():
                if args.copy_source:
                    if not target_audio.exists():
                        shutil.copy2(audio_path, target_audio)
                    source_action = "copied"
                else:
                    # default for asset mode: move source
                    do_move = args.move_source or not args.copy_source
                    if do_move:
                        if target_audio.exists():
                            source_action = "already-in-asset"
                        else:
                            shutil.move(str(audio_path), str(target_audio))
                            source_action = "moved"
                    else:
                        source_action = "kept"
            else:
                source_action = "already-in-asset"

            source_audio_for_model = target_audio if target_audio.exists() else audio_path
            transcript_path = asset_dir / "01_transcript__inbox.md"
            if transcript_path.exists() and not args.overwrite:
                print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {transcript_path.name}")
                continue
        else:
            if out_path.exists() and not args.overwrite:
                print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {audio_path.name}")
                continue

        print(f"[{i}/{len(audio_files)}] {source_audio_for_model.name} ...")

        def do_transcribe_local(lang: str | None, vad_enabled: bool) -> str:
            effective_lang = None if (lang is None or lang == "auto") else lang
            kwargs = {
                "language": effective_lang,
                "beam_size": args.beam_size,
                "best_of": args.best_of,
                "temperature": args.temperature,
                "vad_filter": vad_enabled,
            }
            if args.initial_prompt:
                kwargs["initial_prompt"] = args.initial_prompt
            segments, _info = whisper_model.transcribe(str(source_audio_for_model), **kwargs)
            return "\n".join(s.text.strip() for s in segments if s.text.strip())

        def do_transcribe_cloud(lang: str | None) -> str:
            return _cloud_transcribe(
                source_audio_for_model,
                api_base=cloud_api_base,
                api_key=cloud_api_key,
                model=effective_model,
                language=lang,
                prompt=args.initial_prompt,
                timeout_sec=args.api_timeout,
            )

        if use_cloud:
            text = do_transcribe_cloud(args.language)
        else:
            text = do_transcribe_local(args.language, args.vad_filter)
            if args.min_text_chars_retry > 0 and len(text.strip()) < args.min_text_chars_retry:
                print(f"  ! short transcript ({len(text.strip())} chars), retry with language=auto/vad=off")
                retry_text = do_transcribe_local(None, False)
                if len(retry_text.strip()) > len(text.strip()):
                    text = retry_text
        if not text.strip():
            if args.existing_asset and meta.get("audio_file"):
                title = slug(Path(str(meta["audio_file"])).stem)
            else:
                title = slug(source_audio_for_model.stem)
        else:
            title = None
        md_audio_path = source_audio_for_model
        if args.existing_asset and meta.get("audio_file"):
            md_audio_path = asset_dir / str(meta["audio_file"])
        md = build_md(
            md_audio_path,
            text or "(нет речи)",
            date,
            title,
            asset_path=asset_dir,
        )

        published_inbox_path: Path | None = None
        if (asset_root or args.existing_asset) and transcript_path:
            transcript_path.write_text(md, encoding="utf-8")
            print(f"  -> {transcript_path.name} (asset)")
            if publish_inbox:
                out_path.write_text(md, encoding="utf-8")
                published_inbox_path = out_path
                print(f"  -> {out_path.name} (inbox)")
            if asset_dir:
                if args.existing_asset:
                    src_name = str(meta.get("audio_file", source_audio_for_model.name))
                    if meta.get("source_audio_path"):
                        src_path = Path(str(meta["source_audio_path"]))
                    else:
                        src_path = asset_dir / src_name
                    asr_in = (
                        source_audio_for_model
                        if source_audio_for_model.resolve() != src_path.resolve()
                        else None
                    )
                else:
                    src_name = source_audio_for_model.name
                    src_path = source_audio_for_model
                    asr_in = None
                update_meta_json(
                    asset_dir / "meta.json",
                    asset_dir=asset_dir,
                    source_audio_name=src_name,
                    source_audio_path=src_path,
                    transcript_file=transcript_path.name,
                    published_inbox_path=published_inbox_path,
                    phase="A",
                    asr_input_path=asr_in,
                )
        else:
            out_path.write_text(md, encoding="utf-8")
            print(f"  -> {out_path.name}")

        if manifest_file:
            ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            if (asset_root or args.existing_asset) and transcript_path and asset_dir:
                inbox_name = out_path.name if publish_inbox else ""
                line = (
                    f"{ts},{source_audio_for_model.resolve()!s},{asset_dir},{transcript_path.name},"
                    f"{inbox_name},{date},{source_action}\n"
                )
            else:
                line = f"{ts},{audio_path.resolve()!s},{out_name},{date}\n"
            with manifest_file.open("a", encoding="utf-8") as f:
                f.write(line)

        if args.sleep_between_seconds > 0:
            time.sleep(args.sleep_between_seconds)

    print("Готово.")


if __name__ == "__main__":
    main()
