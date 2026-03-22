#!/usr/bin/env python3
"""
Транскрибация mp3 в .md для Obsidian vault (00_inbox).
Использует faster-whisper с моделью large-v3 для максимального качества.
Требуется GPU с 6+ ГБ VRAM (например RTX 3060).
"""
from pathlib import Path
import argparse
import re
from datetime import datetime

from faster_whisper import WhisperModel


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
    m = re.search(r"(20\d{2})[-]?(0?[1-9]|1[0-2])[-]?(0?[1-9]|[12]\d|3[01])", name)
    if m:
        y, mon, d = m.groups()
        return f"{y}-{mon.zfill(2)}-{d.zfill(2)}"
    try:
        return datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d")
    except OSError:
        return datetime.now().strftime("%Y-%m-%d")


def build_md(audio_path: Path, text: str, date: str, title: str | None) -> str:
    """Собирает .md с frontmatter под шаблон транскрипта Obsidian."""
    audio_name = audio_path.name
    yaml = f"""---
type: transcript
source: audio
audio_file: "{audio_name}"
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Транскрибация mp3 → .md для Obsidian 00_inbox")
    ap.add_argument("input_dir", type=Path, help="Папка с .mp3 (или корень с подпапками при --recursive)")
    ap.add_argument("output_dir", type=Path, help="Папка для .md (например vault/00_inbox)")
    ap.add_argument("--model", default="large-v3", help="Модель faster-whisper (default: large-v3)")
    ap.add_argument("--device", default="cuda", choices=("cuda", "cpu"))
    ap.add_argument("--compute-type", default="float16", help="float16 для 6GB VRAM")
    ap.add_argument("--language", default="ru", help="Язык (ru, auto, ...)")
    ap.add_argument("--overwrite", action="store_true", help="Перезаписывать существующие .md")
    ap.add_argument("--recursive", action="store_true", help="Обходить подпапки (recordings/2024-01, 2024-02, …)")
    ap.add_argument("--manifest", type=Path, default=None, metavar="FILE", help="Лог обработанных: CSV (timestamp, mp3_path, md_name, date)")
    ap.add_argument("--ext", default=".mp3", help="Расширение файлов (default: .mp3)")
    args = ap.parse_args()

    input_dir = args.input_dir.resolve()
    output_dir = args.output_dir.resolve()
    if not input_dir.is_dir():
        raise SystemExit(f"Не найдена папка: {input_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.recursive:
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

    print(f"Загрузка модели {args.model} ({args.device}, {args.compute_type})...")
    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    print(f"Обработка {len(audio_files)} файлов -> {output_dir}")

    manifest_file = None
    if args.manifest:
        manifest_file = args.manifest.resolve()
        if not manifest_file.exists():
            manifest_file.write_text("timestamp,mp3_path,md_name,date\n", encoding="utf-8")

    for i, audio_path in enumerate(audio_files, 1):
        date = date_from_path(audio_path)
        out_name = out_name_for(audio_path)
        out_path = output_dir / out_name
        if out_path.exists() and not args.overwrite:
            print(f"[{i}/{len(audio_files)}] Пропуск (уже есть): {audio_path.name}")
            continue

        print(f"[{i}/{len(audio_files)}] {audio_path.name} ...")
        segments, info = model.transcribe(str(audio_path), language=args.language)
        text = "\n".join(s.text.strip() for s in segments if s.text.strip())
        title = slug(audio_path.stem) if not text else None
        md = build_md(audio_path, text or "(нет речи)", date, title)
        out_path.write_text(md, encoding="utf-8")
        print(f"  -> {out_path.name}")

        if manifest_file:
            ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            line = f"{ts},{audio_path.resolve()!s},{out_name},{date}\n"
            with manifest_file.open("a", encoding="utf-8") as f:
                f.write(line)

    print("Готово.")


if __name__ == "__main__":
    main()
