#!/usr/bin/env python3
"""
Сравнение папки с mp3 и папки 00_inbox: какие записи ещё без .md.
Логика имён .md должна совпадать с transcribe_to_obsidian.py (флаги --recursive / без).
"""
from pathlib import Path
import argparse

from naming import get_expected_md_name


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Проверка: для каждого mp3 есть ли соответствующий .md в 00_inbox"
    )
    ap.add_argument("recordings_dir", type=Path, help="Корень папки записей (как у transcribe)")
    ap.add_argument("inbox_dir", type=Path, help="Папка 00_inbox с .md")
    ap.add_argument(
        "--recursive",
        action="store_true",
        help="Тот же режим, что при транскрибации (--recursive)",
    )
    ap.add_argument("--ext", default=".mp3", help="Расширение (default: .mp3)")
    args = ap.parse_args()

    rec = args.recordings_dir.resolve()
    inbox = args.inbox_dir.resolve()
    if not rec.is_dir():
        raise SystemExit(f"Не найдена папка: {rec}")
    if not inbox.is_dir():
        raise SystemExit(f"Не найдена папка: {inbox}")

    if args.recursive:
        mp3_files = sorted(rec.rglob(f"*{args.ext}"))
    else:
        mp3_files = sorted(rec.glob(f"*{args.ext}"))

    inbox_mds = {p.name for p in inbox.glob("*.md")}
    missing = []
    for p in mp3_files:
        name = get_expected_md_name(p, rec, args.recursive)
        if name not in inbox_mds:
            missing.append((p, name))

    print(f"mp3 найдено: {len(mp3_files)}")
    print(f".md в inbox: {len(inbox_mds)}")
    if not missing:
        print("Все mp3 имеют ожидаемый .md в inbox (по правилам имён).")
        return

    print(f"Без .md (ожидаемое имя): {len(missing)}")
    for mp3_path, md_name in missing:
        print(f"  MISSING  {mp3_path}")
        print(f"           -> {md_name}")


if __name__ == "__main__":
    main()
