#!/usr/bin/env python3
"""
Импорт новых записей с телефона (через Google Drive) в локальный workflow.

Поддерживает 2 источника:
1) Локальная папка (например, синхронизированная Google Drive for Desktop).
2) Rclone remote:path (опционально, если rclone установлен).

После импорта:
- файлы раскладываются в recordings/YYYY-MM/
- имена нормализуются к шаблону YYYY-MM-DD_NNN[_slug].ext
- ведётся manifest CSV
- опционально запускается текущий Phase A (transcribe_to_obsidian.py)
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path


AUDIO_EXTS = {".mp3", ".m4a", ".wav", ".aac", ".flac", ".ogg", ".opus", ".mp4"}
DATE_RE = re.compile(r"(20\d{2})[-_]?([01]\d)[-_]?([0-3]\d)")


def slug(text: str) -> str:
    text = text.strip()
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text[:80] if text else "note"


def extract_date(path: Path) -> str:
    m = DATE_RE.search(path.stem)
    if m:
        y, mon, day = m.groups()
        try:
            dt = datetime(int(y), int(mon), int(day))
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")


def read_existing_day_sequences(month_dir: Path, day: str) -> set[int]:
    used: set[int] = set()
    if not month_dir.exists():
        return used
    for p in month_dir.iterdir():
        if not p.is_file():
            continue
        m = re.match(rf"{re.escape(day)}_(\d{{3}})(?:_|\.|$)", p.name)
        if m:
            used.add(int(m.group(1)))
    return used


def next_sequence(used: set[int]) -> int:
    n = 1
    while n in used:
        n += 1
    used.add(n)
    return n


def source_iter(src_dir: Path, recursive: bool) -> list[Path]:
    if recursive:
        candidates = sorted(p for p in src_dir.rglob("*") if p.is_file())
    else:
        candidates = sorted(p for p in src_dir.iterdir() if p.is_file())
    return [p for p in candidates if p.suffix.lower() in AUDIO_EXTS]


def ensure_manifest_header(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "timestamp",
                "source_id",
                "source_file",
                "target_file",
                "date",
                "sequence",
                "import_mode",
            ]
        )


def read_existing_source_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        has_source_id = "source_id" in fieldnames
        for row in reader:
            if has_source_id:
                value = (row.get("source_id") or "").strip()
                if value:
                    ids.add(value)
                    continue
            # Backward compatibility for old manifests without source_id.
            fallback = (row.get("source_file") or "").strip()
            if fallback:
                ids.add(f"legacy:{fallback}")
    return ids


def rclone_copy(remote: str, remote_path: str, dst: Path) -> None:
    src = f"{remote}:{remote_path}".rstrip(":")
    cmd = ["rclone", "copy", src, str(dst), "--create-empty-src-dirs"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise SystemExit(
            "Rclone copy failed.\n"
            f"Command: {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\n"
            f"stderr:\n{proc.stderr}"
        )


def build_transcribe_cmd(
    script_dir: Path,
    recordings_dir: Path,
    inbox_dir: Path,
    asset_root: Path | None,
    overwrite: bool,
) -> list[str]:
    cmd = [
        sys.executable,
        str(script_dir / "transcribe_to_obsidian.py"),
        str(recordings_dir),
        str(inbox_dir),
        "--recursive",
    ]
    if asset_root:
        cmd.extend(["--asset-root", str(asset_root)])
    if overwrite:
        cmd.append("--overwrite")
    return cmd


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Import phone audio from Google Drive source into recordings/YYYY-MM and optionally run transcription."
    )
    src_group = ap.add_mutually_exclusive_group(required=True)
    src_group.add_argument(
        "--source-dir",
        type=Path,
        help="Локальная папка-источник (например Google Drive Desktop sync folder).",
    )
    src_group.add_argument("--rclone-remote", help="Имя rclone remote (например gdrive).")
    ap.add_argument("--rclone-path", default="", help="Путь в rclone remote (если выбран --rclone-remote).")

    ap.add_argument("--recordings-dir", type=Path, required=True, help="Корень recordings (например D:\\...\\recordings).")
    ap.add_argument("--manifest", type=Path, default=None, help="CSV лог импорта.")
    ap.add_argument("--recursive", action="store_true", help="Рекурсивный поиск в source-dir.")
    ap.add_argument("--copy", action="store_true", help="Копировать из источника (по умолчанию перемещать).")
    ap.add_argument("--dry-run", action="store_true", help="Показать действия без копирования/перемещения.")
    ap.add_argument(
        "--start-transcription",
        action="store_true",
        help="После импорта запустить transcribe_to_obsidian.py по recordings-dir.",
    )
    ap.add_argument("--inbox-dir", type=Path, default=None, help="Обязателен при --start-transcription.")
    ap.add_argument("--asset-root", type=Path, default=None, help="Прокинуть --asset-root в transcribe_to_obsidian.py.")
    ap.add_argument("--overwrite-transcripts", action="store_true", help="Прокинуть --overwrite в транскрибацию.")
    args = ap.parse_args()

    if args.rclone_remote and not shutil.which("rclone"):
        raise SystemExit("rclone не найден в PATH.")
    if args.start_transcription and not args.inbox_dir:
        raise SystemExit("--inbox-dir обязателен вместе с --start-transcription.")

    recordings_dir = args.recordings_dir.resolve()
    recordings_dir.mkdir(parents=True, exist_ok=True)

    work_source_dir: Path
    temp_dir_obj = None
    import_mode = "copy" if args.copy else "move"
    if args.source_dir:
        work_source_dir = args.source_dir.resolve()
        if not work_source_dir.is_dir():
            raise SystemExit(f"Не найдена source dir: {work_source_dir}")
    else:
        temp_dir_obj = tempfile.TemporaryDirectory(prefix="phone-drive-")
        work_source_dir = Path(temp_dir_obj.name)
        rclone_copy(args.rclone_remote, args.rclone_path, work_source_dir)
        import_mode = "rclone-copy"

    candidates = source_iter(work_source_dir, recursive=args.recursive or bool(args.rclone_remote))
    if not candidates:
        print(f"Нет аудиофайлов в источнике: {work_source_dir}")
        return

    manifest_path = args.manifest.resolve() if args.manifest else recordings_dir / "phone_ingest_manifest.csv"
    ensure_manifest_header(manifest_path)
    imported_source_ids = read_existing_source_ids(manifest_path)

    used_by_day: dict[tuple[Path, str], set[int]] = defaultdict(set)
    imported = 0
    skipped = 0
    ts = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    for src in candidates:
        if args.rclone_remote:
            source_id = src.relative_to(work_source_dir).as_posix()
        elif args.source_dir:
            source_id = src.relative_to(work_source_dir).as_posix()
        else:
            source_id = str(src)

        legacy_id = f"legacy:{str(src)}"
        if source_id in imported_source_ids or legacy_id in imported_source_ids:
            print(f"SKIP (already imported): {src}")
            skipped += 1
            continue

        day = extract_date(src)
        month = day[:7]
        month_dir = recordings_dir / month
        month_dir.mkdir(parents=True, exist_ok=True)

        key = (month_dir, day)
        if not used_by_day[key]:
            used_by_day[key] = read_existing_day_sequences(month_dir, day)
        seq = next_sequence(used_by_day[key])

        label = slug(src.stem)
        base_name = f"{day}_{seq:03d}"
        target_name = f"{base_name}_{label}{src.suffix.lower()}" if label and label != "note" else f"{base_name}{src.suffix.lower()}"
        dst = month_dir / target_name

        print(f"{src} -> {dst}")
        if not args.dry_run:
            if args.copy or args.rclone_remote:
                shutil.copy2(src, dst)
            else:
                shutil.move(str(src), str(dst))

            with manifest_path.open("a", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([ts, source_id, str(src), str(dst), day, f"{seq:03d}", import_mode])
                imported_source_ids.add(source_id)
        imported += 1

    print(f"Импортировано: {imported}, пропущено: {skipped}. Manifest: {manifest_path}")

    if args.start_transcription and imported > 0 and not args.dry_run:
        script_dir = Path(__file__).resolve().parent
        cmd = build_transcribe_cmd(
            script_dir=script_dir,
            recordings_dir=recordings_dir,
            inbox_dir=args.inbox_dir.resolve(),
            asset_root=args.asset_root.resolve() if args.asset_root else None,
            overwrite=args.overwrite_transcripts,
        )
        print("Запуск транскрибации:")
        print(subprocess.list2cmdline(cmd))
        proc = subprocess.run(cmd, cwd=script_dir)
        if proc.returncode != 0:
            raise SystemExit(f"Транскрибация завершилась с кодом {proc.returncode}")

    if temp_dir_obj is not None:
        temp_dir_obj.cleanup()


if __name__ == "__main__":
    main()
