#!/usr/bin/env python3
"""Generate docs/archive-index.md for course repos with archive/canvas-submissions."""

from __future__ import annotations

import re
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]

SKIP = {
    "college-projects",
    "IA 103 - Information Security Overview",
    "COSC 111 - Programming and Data Structures",
    "CET 151 - Intro to Computing in Engineering Tech",
}

ARCHIVE_PATHS = (
    ("archive/canvas-submissions", "canvas-submissions"),
    ("archive/course-materials", "course-materials"),
)


def course_title(readme: Path) -> str:
    first = readme.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    return re.sub(r"^#\s*", "", first).strip()


def list_archive(archive: Path) -> list[Path]:
    if not archive.is_dir():
        return []
    files = [p for p in archive.iterdir() if p.is_file() and not p.name.startswith("~$")]
    return sorted(files, key=lambda p: p.name.lower())


def write_index(course_dir: Path) -> bool:
    sections: list[tuple[str, str, list[Path]]] = []
    for subpath, label in ARCHIVE_PATHS:
        archive = course_dir.joinpath(*subpath.split("/"))
        files = list_archive(archive)
        if files:
            sections.append((label, subpath, files))
    if not sections:
        return False

    readme = course_dir / "README.md"
    title = course_title(readme) if readme.exists() else course_dir.name
    docs = course_dir / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    out = docs / "archive-index.md"

    lines = [
        f"# Archive index — {title}",
        "",
        "Readable map of files under `archive/`.",
        "Original PDF/DOCX submissions from Canvas; open the linked file for full content.",
        "",
    ]
    for label, subpath, files in sections:
        lines.extend([f"## {label}", "", "| File | Type |", "|------|------|"])
        for f in files:
            rel = f"../{subpath}/{f.name.replace(' ', '%20')}"
            ext = f.suffix.lower().lstrip(".") or "file"
            lines.append(f"| [{f.name}]({rel}) | {ext} |")
        lines.append("")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Filenames match Canvas export names (including duplicates like `-1` copies).",
            "- Prefer markdown in `docs/` when available; this index is the fallback catalog.",
            "",
        ]
    )
    out.write_text("\n".join(lines), encoding="utf-8")
    return True


def patch_readme(course_dir: Path) -> bool:
    readme = course_dir / "README.md"
    if not readme.exists():
        return False
    text = readme.read_text(encoding="utf-8", errors="replace")
    if "docs/archive-index.md" in text:
        return False
    needles = [
        "| [`archive/canvas-submissions/`](archive/canvas-submissions/) |",
        "| [`archive/course-materials/`](archive/course-materials/) |",
    ]
    insert_line = "| [Archive index](docs/archive-index.md) | Catalog of files in `archive/` with direct links |\n"
    changed = False
    for needle in needles:
        if needle in text:
            text = text.replace(needle, insert_line + needle, 1)
            changed = True
    if changed:
        readme.write_text(text, encoding="utf-8")
    return changed


def main() -> None:
    for course_dir in sorted(WORKSPACE.iterdir()):
        if not course_dir.is_dir() or course_dir.name in SKIP:
            continue
        if not (course_dir / ".git").exists():
            continue
        if write_index(course_dir):
            patch_readme(course_dir)
            print(f"index: {course_dir.name}")


if __name__ == "__main__":
    main()
