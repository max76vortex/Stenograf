from __future__ import annotations

import re
from pathlib import Path


def slugify(text: str) -> str:
    """Return the canonical safe file-name slug used by Phase A outputs."""
    text = text.strip()
    text = re.sub(r"[^\w\s\-]", "", text, flags=re.UNICODE)
    text = re.sub(r"[-\s]+", "-", text).strip("-") or "transcript"
    return text[:120]


def get_expected_md_name(audio_path: Path, root_dir: Path, recursive: bool) -> str:
    if recursive:
        rel = audio_path.relative_to(root_dir)
        stem = rel.with_suffix("").as_posix().replace("/", "_")
        return slugify(stem) + ".md"
    return slugify(audio_path.stem) + ".md"


# Backward-compatible aliases for existing callers.
def slug(text: str) -> str:
    return slugify(text)


def expected_md_name(audio_path: Path, recordings_root: Path, recursive: bool) -> str:
    return get_expected_md_name(audio_path, recordings_root, recursive)
