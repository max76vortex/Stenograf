#!/usr/bin/env python3
"""
Транскрибация mp3 в .md для Obsidian vault (00_inbox).
Использует ASR provider abstraction; текущий default — faster-whisper-local.
Требуется GPU с 6+ ГБ VRAM (например RTX 3060).
"""
from pathlib import Path
import argparse
import csv
import json
import re
import shutil
import time
from datetime import datetime

from asr_providers import (
    DEFAULT_ASR_PROVIDER_ID,
    SUPPORTED_ASR_PROVIDER_IDS,
    AsrError,
    AsrRequest,
    get_provider,
)
from naming import get_expected_md_name, slugify


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
    base = slugify(audio_path.stem)
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
    asr_provider: str = "",
    asr_model: str = "",
    asr_status: str = "success",
    quality_flags: list[str] | None = None,
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
    if asr_provider:
        ver["asr_provider"] = asr_provider
    if asr_model:
        ver["asr_model"] = asr_model
    ver["asr_status"] = asr_status
    if quality_flags:
        ver["quality_flags"] = quality_flags
    versions.append(ver)
    data.update(
        {
            "phase": phase,
            "audio_file": source_audio_name,
            "source_audio_path": str(source_audio_path),
            "asset_path": str(asset_dir),
            "updated_at": now_iso,
            "versions": versions,
            "asr_status": asr_status,
        }
    )
    if asr_provider:
        data["asr_provider"] = asr_provider
    if asr_model:
        data["asr_model"] = asr_model
    if quality_flags:
        data["quality_flags"] = quality_flags
    if "created_at" not in data:
        data["created_at"] = now_iso
    meta_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_asr_failure_meta(
    meta_path: Path,
    *,
    asset_dir: Path,
    source_audio_name: str,
    source_audio_path: Path,
    asr_input_path: Path | None,
    error: AsrError,
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
        "phase": "A",
        "asr_status": "failed",
        "transcript_file": "",
        "published_inbox_path": "",
        "asr_provider": error.provider_id,
        "asr_model": error.model,
        "asr_error_category": error.category,
        "asr_error_message": error.message,
    }
    if asr_input_path is not None and asr_input_path.resolve() != source_audio_path.resolve():
        ver["asr_input"] = str(asr_input_path.resolve())
    versions.append(ver)
    data.update(
        {
            "phase": "A",
            "audio_file": source_audio_name,
            "source_audio_path": str(source_audio_path),
            "asset_path": str(asset_dir),
            "updated_at": now_iso,
            "versions": versions,
            "asr_status": "failed",
            "asr_provider": error.provider_id,
            "asr_model": error.model,
            "asr_error_category": error.category,
            "asr_error_message": error.message,
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
{title or slugify(audio_path.stem)}

## Краткое резюме (заполнить после просмотра)
- **Основные темы**:
- **Ключевые идеи**:
- **Направления**: статьи / проекты / задачи / личное

## Транскрипт

{text}
"""
    return yaml


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "Transcribe audio files to Markdown for Obsidian 00_inbox "
            f"(default ASR provider: {DEFAULT_ASR_PROVIDER_ID})."
        )
    )
    ap.add_argument("input_dir", type=Path, help="Папка с .mp3 (или корень с подпапками при --recursive)")
    ap.add_argument("output_dir", type=Path, help="Папка для .md (например vault/00_inbox)")
    ap.add_argument("--model", default="large-v3", help="ASR model/profile (default: large-v3)")
    ap.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    ap.add_argument("--compute-type", default="float16", help="float16 для 6GB VRAM")
    ap.add_argument("--language", default="ru", help="Язык (ru, auto, ...)")
    ap.add_argument(
        "--asr-provider",
        default=DEFAULT_ASR_PROVIDER_ID,
        choices=sorted(SUPPORTED_ASR_PROVIDER_IDS),
        help=f"ASR provider id (default: {DEFAULT_ASR_PROVIDER_ID})",
    )
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
    ap.add_argument("--beam-size", type=int, default=5, help="Beam size for decoding (default: 5)")
    ap.add_argument("--best-of", type=int, default=5, help="Best-of candidates (default: 5)")
    ap.add_argument("--temperature", type=float, default=0.0, help="Decoding temperature (default: 0.0)")
    ap.add_argument("--vad-filter", action="store_true", help="Use VAD filtering before decoding")
    ap.add_argument("--initial-prompt", default="", help="Optional initial prompt for model context")
    ap.add_argument(
        "--min-text-chars-retry",
        type=int,
        default=0,
        metavar="N",
        help="If transcript shorter than N chars, retry once with language=auto and VAD off",
    )
    ap.add_argument(
        "--existing-asset",
        action="store_true",
        help="input_dir — уже существующая папка ассета: пишет 01_transcript__inbox.md + inbox; без копирования/переноса",
    )
    args = ap.parse_args()

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
            return slugify(p.stem) + ".md"
    elif args.recursive:
        audio_files = sorted(input_dir.rglob(f"*{args.ext}"))
        def out_name_for(p: Path) -> str:
            return get_expected_md_name(p, input_dir, recursive=True)
    else:
        audio_files = sorted(input_dir.glob(f"*{args.ext}"))
        def out_name_for(p: Path) -> str:
            return get_expected_md_name(p, input_dir, recursive=False)
    if not audio_files:
        print(f"Нет файлов *{args.ext} в {input_dir}")
        return

    asset_root = args.asset_root.resolve() if args.asset_root else None
    publish_inbox = not args.no_publish_inbox
    if asset_root:
        asset_root.mkdir(parents=True, exist_ok=True)
    if args.copy_source and args.move_source:
        raise SystemExit("Нельзя использовать одновременно --copy-source и --move-source")

    print(f"Загрузка ASR provider {args.asr_provider}: {args.model} ({args.device}, {args.compute_type})...")
    try:
        asr_provider = get_provider(
            args.asr_provider,
            model=args.model,
            device=args.device,
            compute_type=args.compute_type,
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    except AsrError as exc:
        raise SystemExit(
            f"ASR provider init failed: {exc.provider_id} {exc.model} "
            f"[{exc.category}] {exc.message}"
        ) from exc
    print(f"Обработка {len(audio_files)} файлов -> {output_dir}")

    manifest_file = None
    if args.manifest:
        manifest_file = args.manifest.resolve()
        if not manifest_file.exists():
            if asset_root or args.existing_asset:
                manifest_file.write_text(
                    "timestamp,mp3_path,asset_dir,transcript_file,inbox_md,date,source_action,"
                    "asr_provider,asr_model,asr_status,asr_error_category,asr_error_message,"
                    "error_category,elapsed_sec\n",
                    encoding="utf-8",
                )
            else:
                manifest_file.write_text(
                    "timestamp,mp3_path,md_name,date,"
                    "asr_provider,asr_model,asr_status,asr_error_category,asr_error_message,"
                    "error_category,elapsed_sec\n",
                    encoding="utf-8",
                )

    failure_count = 0
    has_errors = False
    for i, audio_path in enumerate(audio_files, 1):
        meta: dict = {}
        date = date_from_path(audio_path)
        out_name = out_name_for(audio_path)
        out_path = output_dir / out_name
        source_action = "none"
        source_audio_for_model = audio_path
        pending_move_target: Path | None = None
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
                out_name = slugify(Path(str(meta["audio_file"])).stem) + ".md"
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
                    source_audio_for_model = target_audio
                else:
                    # Defer destructive move until ASR succeeds, so a failed file remains retryable
                    # by rerunning the same recordings -> asset-root command.
                    do_move = args.move_source or not args.copy_source
                    if do_move:
                        if target_audio.exists():
                            source_action = "already-in-asset"
                            source_audio_for_model = target_audio
                        else:
                            pending_move_target = target_audio
                            source_action = "moved"
                    else:
                        source_action = "kept"
            else:
                source_action = "already-in-asset"
                source_audio_for_model = target_audio
            transcript_path = asset_dir / "01_transcript__inbox.md"
            if transcript_path.exists() and not args.overwrite:
                print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {transcript_path.name}")
                continue
        else:
            if out_path.exists() and not args.overwrite:
                print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {audio_path.name}")
                continue

        src_name_for_meta = source_audio_for_model.name
        src_path_for_meta = source_audio_for_model
        asr_in_for_meta: Path | None = None
        if asset_dir:
            if args.existing_asset:
                src_name_for_meta = str(meta.get("audio_file", source_audio_for_model.name))
                if meta.get("source_audio_path"):
                    src_path_for_meta = Path(str(meta["source_audio_path"]))
                else:
                    src_path_for_meta = asset_dir / src_name_for_meta
                asr_in_for_meta = (
                    source_audio_for_model
                    if source_audio_for_model.resolve() != src_path_for_meta.resolve()
                    else None
                )
            else:
                src_name_for_meta = source_audio_for_model.name
                src_path_for_meta = source_audio_for_model

        print(f"[{i}/{len(audio_files)}] {source_audio_for_model.name} ...")

        asr_request_audio_path = source_audio_for_model
        request = AsrRequest(
            audio_path=asr_request_audio_path,
            language=args.language,
            provider_id=args.asr_provider,
            model=args.model,
            runtime_options={
                "device": args.device,
                "compute_type": args.compute_type,
                "beam_size": args.beam_size,
                "best_of": args.best_of,
                "temperature": args.temperature,
                "vad_filter": args.vad_filter,
                "initial_prompt": args.initial_prompt,
                "min_text_chars_retry": args.min_text_chars_retry,
            },
            source_metadata={
                "source_audio_name": audio_path.name,
                "output_name": out_name,
                "asset_dir": str(asset_dir) if asset_dir else "",
                "source_action": source_action,
            },
        )
        try:
            transcribe_started = time.perf_counter()
            asr_result = asr_provider.transcribe(request)
        except AsrError as exc:
            elapsed_sec = round(time.perf_counter() - transcribe_started, 3)
            failure_count += 1
            has_errors = True
            print(
                f"[FAILED] {source_audio_for_model.name}: "
                f"{exc.provider_id} {exc.model} [{exc.category}] {exc.message}"
            )
            if asset_dir:
                update_asr_failure_meta(
                    asset_dir / "meta.json",
                    asset_dir=asset_dir,
                    source_audio_name=src_name_for_meta,
                    source_audio_path=src_path_for_meta,
                    asr_input_path=asr_in_for_meta,
                    error=exc,
                )
            if manifest_file:
                ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                with manifest_file.open("a", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    if (asset_root or args.existing_asset) and asset_dir:
                        writer.writerow(
                            [
                                ts,
                                str(source_audio_for_model.resolve()),
                                str(asset_dir),
                                "",
                                "",
                                date,
                                source_action,
                                exc.provider_id,
                                exc.model,
                                "failed",
                                exc.category,
                                exc.message,
                                exc.category,
                                elapsed_sec,
                            ]
                        )
                    else:
                        writer.writerow(
                            [
                                ts,
                                str(audio_path.resolve()),
                                out_name,
                                date,
                                exc.provider_id,
                                exc.model,
                                "failed",
                                exc.category,
                                exc.message,
                                exc.category,
                                elapsed_sec,
                            ]
                        )
            continue
        elapsed_sec = round(time.perf_counter() - transcribe_started, 3)
        if pending_move_target is not None:
            shutil.move(str(audio_path), str(pending_move_target))
            source_audio_for_model = pending_move_target
            src_name_for_meta = source_audio_for_model.name
            src_path_for_meta = source_audio_for_model
            asr_in_for_meta = asr_request_audio_path
        text = asr_result.text
        if not text.strip():
            if args.existing_asset and meta.get("audio_file"):
                title = slugify(Path(str(meta["audio_file"])).stem)
            else:
                title = slugify(source_audio_for_model.stem)
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
                update_meta_json(
                    asset_dir / "meta.json",
                    asset_dir=asset_dir,
                    source_audio_name=src_name_for_meta,
                    source_audio_path=src_path_for_meta,
                    transcript_file=transcript_path.name,
                    published_inbox_path=published_inbox_path,
                    phase="A",
                    asr_input_path=asr_in_for_meta,
                    asr_provider=asr_result.provider_id,
                    asr_model=asr_result.model,
                    asr_status="success",
                    quality_flags=asr_result.quality_flags,
                )
        else:
            out_path.write_text(md, encoding="utf-8")
            print(f"  -> {out_path.name}")

        if manifest_file:
            ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            with manifest_file.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                if (asset_root or args.existing_asset) and transcript_path and asset_dir:
                    inbox_name = out_path.name if publish_inbox else ""
                    writer.writerow(
                        [
                            ts,
                            str(source_audio_for_model.resolve()),
                            str(asset_dir),
                            transcript_path.name,
                            inbox_name,
                            date,
                            source_action,
                            asr_result.provider_id,
                            asr_result.model,
                            "success",
                            "",
                            "",
                            "",
                            elapsed_sec,
                        ]
                    )
                else:
                    writer.writerow(
                        [
                            ts,
                            str(audio_path.resolve()),
                            out_name,
                            date,
                            asr_result.provider_id,
                            asr_result.model,
                            "success",
                            "",
                            "",
                            "",
                            elapsed_sec,
                        ]
                    )

        if args.sleep_between_seconds > 0:
            time.sleep(args.sleep_between_seconds)

    if has_errors:
        print(f"Готово с ошибками: failed={failure_count}.")
        raise SystemExit(1)
    print("Готово.")


if __name__ == "__main__":
    main()
