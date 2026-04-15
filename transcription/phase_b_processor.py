#!/usr/bin/env python3
"""
Phase B processor (LLM-first):
- reads asset folders created after Phase A
- builds cleaned text (02_clean__review.md)
- classifies content into idea/article/project
- writes classified file (03_content__{category}.md)
- updates meta.json
- optionally publishes classified file to Obsidian 10_processed/*

Default LLM backend: Ollama HTTP API. По умолчанию **не** передаём `options.num_gpu`
(автовыбор слоёв на GPU у Ollama). Явное `num_gpu=999` у части моделей даёт ошибку
«memory layout cannot be allocated» — используйте `--ollama-num-gpu N` или `--cpu-only`.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path


ALLOWED_CATEGORIES = ("idea", "article", "project")
CATEGORY_TO_PROCESSED_DIR = {
    "idea": "ideas",
    "article": "articles",
    "project": "projects",
}
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_STYLE_PROFILE = SCRIPT_DIR / "style" / "style_profile.md"
DEFAULT_EDITING_CHECKLIST = SCRIPT_DIR / "style" / "editing_checklist.md"
DEFAULT_STYLE_EXAMPLES_DIR = SCRIPT_DIR / "style" / "examples"

def slug(s: str) -> str:
    s = s.strip()
    s = re.sub(r"[^\w\s\-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[-\s]+", "-", s).strip("-") or "content"
    return s[:120]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def load_style_examples(examples_dir: Path, max_files: int = 5, max_chars: int = 8000) -> str:
    if not examples_dir.exists():
        return ""
    files = sorted([p for p in examples_dir.iterdir() if p.is_file() and p.suffix.lower() in (".md", ".txt")])
    chunks: list[str] = []
    total = 0
    for p in files[:max_files]:
        text = read_text(p).strip()
        if not text:
            continue
        block = f"[EXAMPLE: {p.name}]\n{text}\n"
        if total + len(block) > max_chars:
            remain = max_chars - total
            if remain <= 0:
                break
            block = block[:remain]
        chunks.append(block)
        total += len(block)
        if total >= max_chars:
            break
    return "\n".join(chunks).strip()


def parse_frontmatter(md_text: str) -> tuple[dict[str, str], str]:
    if not md_text.startswith("---\n"):
        return {}, md_text
    end = md_text.find("\n---\n", 4)
    if end == -1:
        return {}, md_text
    raw = md_text[4:end].splitlines()
    body = md_text[end + 5 :]
    fm: dict[str, str] = {}
    for line in raw:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"')
    return fm, body


def extract_transcript(body: str) -> str:
    marker = "## Транскрипт"
    idx = body.find(marker)
    if idx == -1:
        return body.strip()
    return body[idx + len(marker) :].strip()


def build_markdown(frontmatter: dict[str, str], title: str, summary: str, text: str) -> str:
    fm_lines = ["---"]
    for key, value in frontmatter.items():
        fm_lines.append(f'{key}: "{value}"')
    fm_lines.append("---")
    return (
        "\n".join(fm_lines)
        + "\n\n## Заголовок\n"
        + title.strip()
        + "\n\n## Краткое резюме\n"
        + (summary.strip() or "-")
        + "\n\n## Текст\n\n"
        + text.strip()
        + "\n"
    )


def default_llm_payload(
    transcript: str,
    style_profile_text: str,
    editing_checklist_text: str,
    style_examples_text: str,
) -> str:
    return (
        "Ты редактор русскоязычных транскриптов.\n"
        "Работай в стиле автора из STYLE_PROFILE и STYLE_EXAMPLES. "
        "Соблюдай чеклист EDITING_CHECKLIST как обязательный стандарт качества.\n"
        "Верни ТОЛЬКО JSON-объект (без markdown) со схемой:\n"
        '{'
        '"title":"...",'
        '"clean_text":"...",'
        '"summary":"...",'
        '"category":"idea|article|project",'
        '"tags":["tag1","tag2"],'
        '"needs_review":true|false,'
        '"review_reason":"..."'
        '}\n'
        "Правила:\n"
        "- Сохраняй смысл оригинала, не выдумывай фактов.\n"
        "- Исправь пунктуацию и очевидные ASR-ошибки.\n"
        "- category=idea для зарисовок, article для наброска публикации, project для задач/планов проекта.\n\n"
        f"STYLE_PROFILE:\n{style_profile_text}\n\n"
        f"EDITING_CHECKLIST:\n{editing_checklist_text}\n\n"
        f"STYLE_EXAMPLES:\n{style_examples_text or '(пока нет примеров)'}\n\n"
        f"Транскрипт:\n{transcript}\n"
    )


def call_ollama_json(
    prompt: str,
    model: str,
    endpoint: str,
    timeout_sec: int,
    ollama_options: dict | None = None,
) -> dict:
    opts = dict(ollama_options) if ollama_options else {}
    payload: dict = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }
    if opts:
        payload["options"] = opts
    req = urllib.request.Request(
        endpoint.rstrip("/") + "/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    raw = json.loads(body)
    if raw.get("error"):
        raise RuntimeError(f"Ollama error: {raw['error']}")
    # qwen3.5 (thinking) с format=json часто кладёт JSON в `thinking`, а `response` пустой
    text = (raw.get("response") or raw.get("thinking") or "").strip()
    if not text:
        raise RuntimeError("Ollama returned empty response and thinking")
    return parse_llm_json_response(text)


def call_openai_compatible_json(
    prompt: str,
    model: str,
    base_url: str,
    timeout_sec: int,
    api_key: str = "",
) -> dict:
    """OpenAI-совместимый чат (LM Studio, vLLM, OpenAI, Groq и т.д.): POST .../v1/chat/completions."""
    url = base_url.rstrip("/") + "/chat/completions"
    payload: dict = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }

    def _post(p: dict) -> str:
        data = json.dumps(p).encode("utf-8")
        headers: dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        req = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            return resp.read().decode("utf-8")

    try:
        body = _post(payload)
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        if exc.code == 400 and "response_format" in payload:
            payload.pop("response_format", None)
            try:
                body = _post(payload)
            except Exception as exc2:
                raise RuntimeError(
                    f"OpenAI-compatible request failed after retry: {exc2} (was: {err_body[:300]})"
                ) from exc2
        else:
            raise RuntimeError(
                f"OpenAI-compatible HTTP {exc.code}: {err_body[:400]}"
            ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"OpenAI-compatible request failed: {exc}") from exc

    raw = json.loads(body)
    if raw.get("error"):
        raise RuntimeError(f"API error: {raw['error']}")
    choices = raw.get("choices")
    if not choices:
        raise RuntimeError("OpenAI-compatible response has no choices")
    msg = choices[0].get("message") or {}
    text = (msg.get("content") or "").strip()
    if not text:
        raise RuntimeError("OpenAI-compatible empty message content")
    return parse_llm_json_response(text)


def parse_llm_json_response(text: str) -> dict:
    """Парсит JSON из ответа Ollama: чистый JSON, блок ```json ...``` или первый объект {...}."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        start = t.find("{")
        end = t.rfind("}")
        if start != -1 and end > start:
            try:
                return json.loads(t[start : end + 1])
            except json.JSONDecodeError:
                pass
        raise RuntimeError(f"LLM returned non-JSON payload: {text[:400]}")


def heuristic_result(transcript: str, stem: str) -> dict:
    low = transcript.lower()
    if any(word in low for word in ("проект", "план", "срок", "этап")):
        category = "project"
    elif any(word in low for word in ("статья", "публикац", "заголовок", "читатель")):
        category = "article"
    else:
        category = "idea"
    clean = re.sub(r"\n{3,}", "\n\n", transcript).strip()
    return {
        "title": stem,
        "clean_text": clean,
        "summary": "Автосводка недоступна (heuristic fallback).",
        "category": category,
        "tags": [category],
        "needs_review": True,
        "review_reason": "LLM недоступна, использован heuristic fallback.",
    }


def ensure_meta(asset_dir: Path) -> tuple[dict, Path]:
    meta_path = asset_dir / "meta.json"
    if meta_path.exists():
        try:
            data = json.loads(read_text(meta_path))
            if isinstance(data, dict):
                return data, meta_path
        except Exception:
            pass
    return {"versions": []}, meta_path


def save_meta(meta: dict, meta_path: Path) -> None:
    write_text(meta_path, json.dumps(meta, ensure_ascii=False, indent=2) + "\n")


def process_asset(
    asset_dir: Path,
    vault_dir: Path | None,
    model: str,
    endpoint: str,
    timeout_sec: int,
    style_profile_text: str,
    editing_checklist_text: str,
    style_examples_text: str,
    allow_heuristic_fallback: bool,
    overwrite: bool,
    ollama_options: dict | None = None,
    *,
    backend: str = "ollama",
    openai_base_url: str = "http://127.0.0.1:1234/v1",
    api_key: str = "",
) -> tuple[bool, str]:
    transcript_path = asset_dir / "01_transcript__inbox.md"
    if not transcript_path.exists():
        return False, "skip: no 01_transcript__inbox.md"

    src_md = read_text(transcript_path)
    fm, body = parse_frontmatter(src_md)
    transcript = extract_transcript(body)
    if not transcript:
        return False, "skip: transcript section is empty"

    prompt = default_llm_payload(
        transcript=transcript,
        style_profile_text=style_profile_text,
        editing_checklist_text=editing_checklist_text,
        style_examples_text=style_examples_text,
    )
    try:
        if backend == "ollama":
            llm = call_ollama_json(
                prompt,
                model,
                endpoint,
                timeout_sec,
                ollama_options=ollama_options,
            )
        elif backend == "openai":
            llm = call_openai_compatible_json(
                prompt,
                model,
                openai_base_url,
                timeout_sec,
                api_key=api_key,
            )
        else:
            raise RuntimeError(f"unknown backend: {backend}")
    except Exception as exc:
        if not allow_heuristic_fallback:
            return False, f"error: LLM failed ({exc})"
        llm = heuristic_result(transcript, asset_dir.name)

    category = str(llm.get("category", "")).strip().lower()
    if category not in ALLOWED_CATEGORIES:
        category = "idea"
        llm["needs_review"] = True
        llm["review_reason"] = "Неизвестная категория от LLM, назначено idea."

    tags = llm.get("tags") if isinstance(llm.get("tags"), list) else []
    tags = [slug(str(t)) for t in tags if str(t).strip()]
    if not tags:
        tags = [category]

    now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    clean_path = asset_dir / "02_clean__review.md"
    content_path = asset_dir / f"03_content__{category}.md"
    if content_path.exists() and not overwrite:
        return False, f"skip: exists {content_path.name}"

    common_fm = {
        "type": category if category != "idea" else "note",
        "status": "review",
        "category": category,
        "audio_file": fm.get("audio_file", ""),
        "asset_path": str(asset_dir),
        "source_transcript": transcript_path.name,
        "tags": ", ".join(tags),
        "updated_at": now_iso,
    }

    clean_md = build_markdown(
        frontmatter={**common_fm, "phase": "B2", "stage": "clean"},
        title=str(llm.get("title", "")).strip() or asset_dir.name,
        summary=str(llm.get("summary", "")).strip() or "-",
        text=str(llm.get("clean_text", "")).strip() or transcript,
    )
    write_text(clean_path, clean_md)

    content_md = build_markdown(
        frontmatter={**common_fm, "phase": "B5", "stage": "classified"},
        title=str(llm.get("title", "")).strip() or asset_dir.name,
        summary=str(llm.get("summary", "")).strip() or "-",
        text=str(llm.get("clean_text", "")).strip() or transcript,
    )
    write_text(content_path, content_md)

    meta, meta_path = ensure_meta(asset_dir)
    meta["phase"] = "B"
    meta["category"] = category
    meta["needs_review"] = bool(llm.get("needs_review", False))
    meta["review_reason"] = str(llm.get("review_reason", "")).strip()
    meta["llm_model"] = model
    meta["llm_backend"] = backend
    if backend == "openai":
        meta["openai_base_url"] = openai_base_url
    if ollama_options and "num_gpu" in ollama_options:
        meta["ollama_num_gpu"] = ollama_options["num_gpu"]
    meta["style_profile"] = "custom"
    meta["updated_at"] = now_iso
    versions = meta.get("versions")
    if not isinstance(versions, list):
        versions = []
    versions.append(
        {
            "timestamp": now_iso,
            "files": [clean_path.name, content_path.name],
            "category": category,
        }
    )
    meta["versions"] = versions
    save_meta(meta, meta_path)

    if vault_dir:
        target = (
            vault_dir
            / "10_processed"
            / CATEGORY_TO_PROCESSED_DIR[category]
            / f"{asset_dir.name}__{category}.md"
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(content_path, target)

    return True, f"ok: {content_path.name} (category={category})"


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Phase B MVP: LLM-first text preparation and classification for asset folders."
    )
    ap.add_argument("asset_root", type=Path, help="Корень asset-папок (например D:\\audio-work)")
    ap.add_argument(
        "--vault-dir",
        type=Path,
        default=None,
        help="Путь к Obsidian vault (если задан, скрипт публикует в 10_processed/*)",
    )
    ap.add_argument(
        "--backend",
        choices=("ollama", "openai"),
        default="ollama",
        help="ollama — /api/generate; openai — OpenAI-совместимый чат (LM Studio: локальный сервер на 1234)",
    )
    ap.add_argument("--model", default="qwen2.5:14b", help="Имя модели в Ollama или в LM Studio (как в UI)")
    ap.add_argument("--ollama-endpoint", default="http://127.0.0.1:11434", help="Базовый URL Ollama (только --backend ollama)")
    ap.add_argument(
        "--openai-base-url",
        default="http://127.0.0.1:1234/v1",
        help="Базовый URL OpenAI API (LM Studio по умолчанию: .../v1)",
    )
    ap.add_argument(
        "--api-key",
        default="",
        help="API-ключ для cloud LLM (OpenAI, Groq и др.). Или переменная OPENAI_API_KEY",
    )
    ap.add_argument(
        "--timeout-sec",
        type=int,
        default=120,
        help="Таймаут HTTP к Ollama (сек). Модели с «thinking» (qwen3.5) и длинные промпты — ставьте 900–1800",
    )
    ap.add_argument(
        "--cpu-only",
        action="store_true",
        help="Не использовать GPU в Ollama (options.num_gpu=0; только CPU/RAM)",
    )
    ap.add_argument(
        "--ollama-num-gpu",
        type=int,
        default=None,
        metavar="N",
        help="Число слоёв на GPU (Ollama options.num_gpu). Без флага — не задаём, Ollama сам выбирает GPU/CPU",
    )
    ap.add_argument("--overwrite", action="store_true", help="Перезаписать 03_content__*.md")
    ap.add_argument(
        "--allow-heuristic-fallback",
        action="store_true",
        help="Если LLM недоступна, использовать heuristic fallback",
    )
    ap.add_argument(
        "--style-profile",
        type=Path,
        default=DEFAULT_STYLE_PROFILE,
        help="Markdown-файл с профилем вашего стиля (обязательно для LLM-прохода).",
    )
    ap.add_argument(
        "--editing-checklist",
        type=Path,
        default=DEFAULT_EDITING_CHECKLIST,
        help="Markdown-файл с редакторским чеклистом (обязательно для LLM-прохода).",
    )
    ap.add_argument(
        "--style-examples-dir",
        type=Path,
        default=DEFAULT_STYLE_EXAMPLES_DIR,
        help="Папка с примерами вашего стиля (.md/.txt), используется в prompt.",
    )
    ap.add_argument(
        "--recursive",
        action="store_true",
        help="Рекурсивно искать asset-папки (по наличию 01_transcript__inbox.md).",
    )
    args = ap.parse_args()

    root = args.asset_root.resolve()
    if not root.is_dir():
        raise SystemExit(f"Не найдена папка: {root}")

    if args.recursive:
        found: list[Path] = []
        for p in sorted(root.rglob("01_transcript__inbox.md")):
            parent = p.parent
            if parent.is_dir():
                found.append(parent)
        # remove duplicates while preserving order
        seen: set[str] = set()
        asset_dirs = []
        for d in found:
            key = str(d.resolve())
            if key in seen:
                continue
            seen.add(key)
            asset_dirs.append(d)
    else:
        asset_dirs = [p for p in sorted(root.iterdir()) if p.is_dir()]
    if not asset_dirs:
        print(f"Нет asset-папок в {root}")
        return

    vault_dir = args.vault_dir.resolve() if args.vault_dir else None
    style_profile_path = args.style_profile.resolve()
    checklist_path = args.editing_checklist.resolve()
    examples_dir = args.style_examples_dir.resolve()
    if not style_profile_path.exists():
        raise SystemExit(f"Не найден style profile: {style_profile_path}")
    if not checklist_path.exists():
        raise SystemExit(f"Не найден editing checklist: {checklist_path}")
    style_profile_text = read_text(style_profile_path)
    editing_checklist_text = read_text(checklist_path)
    style_examples_text = load_style_examples(examples_dir)
    if args.backend == "ollama":
        if args.cpu_only and args.ollama_num_gpu is not None:
            raise SystemExit("Нельзя одновременно --cpu-only и --ollama-num-gpu")
        if args.cpu_only:
            ollama_options: dict[str, int] | None = {"num_gpu": 0}
        elif args.ollama_num_gpu is not None:
            ollama_options = {"num_gpu": args.ollama_num_gpu}
        else:
            ollama_options = None
    else:
        if args.cpu_only or args.ollama_num_gpu is not None:
            raise SystemExit("Флаги --cpu-only / --ollama-num-gpu только для --backend ollama")
        ollama_options = None

    resolved_api_key = args.api_key or os.environ.get("OPENAI_API_KEY", "")

    ok_count = 0
    skip_count = 0
    err_count = 0

    if args.backend == "ollama":
        opt_desc = (
            f"num_gpu={ollama_options['num_gpu']}"
            if ollama_options
            else "num_gpu не задан (автовыбор Ollama)"
        )
        print(f"Phase B: backend=ollama, {len(asset_dirs)} asset-папок ({opt_desc})")
    else:
        print(
            f"Phase B: backend=openai ({args.openai_base_url}), "
            f"{len(asset_dirs)} asset-папок, model={args.model!r}"
        )
    for i, asset in enumerate(asset_dirs, 1):
        ok, message = process_asset(
            asset_dir=asset,
            vault_dir=vault_dir,
            model=args.model,
            endpoint=args.ollama_endpoint,
            timeout_sec=args.timeout_sec,
            style_profile_text=style_profile_text,
            editing_checklist_text=editing_checklist_text,
            style_examples_text=style_examples_text,
            allow_heuristic_fallback=args.allow_heuristic_fallback,
            overwrite=args.overwrite,
            ollama_options=ollama_options,
            backend=args.backend,
            openai_base_url=args.openai_base_url,
            api_key=resolved_api_key,
        )
        if message.startswith("ok:"):
            ok_count += 1
        elif message.startswith("skip:"):
            skip_count += 1
        else:
            err_count += 1
        print(f"[{i}/{len(asset_dirs)}] {asset.name}: {message}")

    print(f"Done. ok={ok_count}, skip={skip_count}, error={err_count}")
    if err_count:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

