#!/usr/bin/env python3
"""
Mirror course repos under ../College Projects PT/ with Portuguese markdown.

Copies full tree (no .git). Translates *.md; preserves ``` fences and inline `code`.
Use --resume to continue without deleting the mirror. Completion markers: *.md.pt.done

  pip install deep-translator
  python scripts/build_portuguese_mirrors.py --resume
  python scripts/build_portuguese_mirrors.py --repo "IA 103 - Information Security Overview" --resume
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
import time
from pathlib import Path

from deep_translator import GoogleTranslator

ROOT_EN = Path(__file__).resolve().parents[2]
ROOT_PT = ROOT_EN.parent / "College Projects PT"
COLLEGE_PROJECTS = ROOT_EN / "college-projects"

REPOS = [
    "CET 151 - Intro to Computing in Engineering Tech",
    "COSC 111 - Programming and Data Structures",
    "COSC 314 - Computational Discrete Structs",
    "COSC 381 - Software Engineering Solutions",
    "Cyber Crime Investigation",
    "IA 103 - Information Security Overview",
    "IA 244 - Administration of Computer Systems",
    "IA 329 - Policy Development Info Assurance",
    "IA 385 - Database Web Application Security",
    "IA 403 - Malware Analysis Reverse Engineering",
    "IA 445 - Ethical Hacking Offensive Security",
    "IA 447 - Digital Forensics I",
    "IA455 - Incident Response",
]

SKIP_DIR_NAMES = {".git", "__pycache__", ".venv", "node_modules"}
CHUNK = 4000
SLEEP_SEC = 0.08

FENCE_RE = re.compile(r"(```[\s\S]*?```)", re.MULTILINE)
INLINE_CODE_RE = re.compile(r"(`[^`\n]+`)")

translator = GoogleTranslator(source="en", target="pt")


def log(msg: str) -> None:
    print(msg, flush=True)


def translate_plain(text: str) -> str:
    if not text.strip():
        return text
    out: list[str] = []
    pos = 0
    while pos < len(text):
        piece = text[pos : pos + CHUNK]
        for attempt in range(5):
            try:
                translated = translator.translate(piece)
                if translated:
                    out.append(translated)
                else:
                    out.append(piece)
                break
            except Exception:
                time.sleep(1.0 * (attempt + 1))
        else:
            out.append(piece)
        pos += CHUNK
        time.sleep(SLEEP_SEC)
    return "".join(out)


def translate_segment(segment: str) -> str:
    if not segment.strip():
        return segment
    parts = INLINE_CODE_RE.split(segment)
    chunks: list[str] = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            chunks.append(part)
        else:
            chunks.append(translate_plain(part))
    return "".join(chunks)


def translate_markdown(content: str) -> str:
    if len(content) > 12_000:
        sections = re.split(r"(?=^## )", content, flags=re.MULTILINE)
        if len(sections) > 1:
            return "".join(
                translate_markdown(s) if not s.startswith("```") else s for s in sections
            )
    blocks = FENCE_RE.split(content)
    result: list[str] = []
    for block in blocks:
        if block.startswith("```"):
            result.append(block)
        else:
            result.append(translate_segment(block))
    return "".join(result)


def copy_tree_fresh(src: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(
        src,
        dest,
        ignore=shutil.ignore_patterns(*SKIP_DIR_NAMES),
        dirs_exist_ok=True,
    )


def sync_tree(src: Path, dest: Path) -> None:
    """Copy missing files from src; do not delete extra files in dest."""
    dest.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in SKIP_DIR_NAMES:
            continue
        target = dest / item.name
        if item.is_dir():
            sync_tree(item, target)
        elif not target.exists():
            shutil.copy2(item, target)


def mirror_repo(name: str, resume: bool, force: bool) -> None:
    src = ROOT_EN / name
    if not src.is_dir():
        log(f"skip missing {name}")
        return
    dest = ROOT_PT / f"{name} (PT)"
    log(f"=== {name} -> {dest.name} ===")
    if resume and dest.exists():
        sync_tree(src, dest)
    else:
        copy_tree_fresh(src, dest)

    meta = {"source": name, "language": "pt-BR", "generated_by": "build_portuguese_mirrors.py"}
    (dest / ".mirror-source.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    readme_note = dest / "LEIA-ME.md"
    if not readme_note.exists():
        readme_note.write_text(
            "# Versão em português (PT-BR)\n\n"
            "Este diretório é um **espelho** do repositório em inglês, com arquivos "
            "`*.md` traduzidos automaticamente. Código, scripts e `archive/` permanecem "
            "iguais. Exportações traduzidas em `docs/canvas-pt/`.\n\n"
            f"**Origem:** `{name}`\n",
            encoding="utf-8",
        )

    md_files = sorted(dest.rglob("*.md"), key=lambda p: (p.name != "README.md", str(p)))
    for md in md_files:
        if md.name == "LEIA-ME.md":
            continue
        done = md.with_suffix(".md.pt.done")
        if resume and done.exists() and not force:
            continue
        original = md.read_text(encoding="utf-8")
        try:
            md.write_text(translate_markdown(original), encoding="utf-8")
            done.write_text("ok", encoding="utf-8")
        except Exception as exc:
            log(f"  WARN {md.relative_to(dest)}: {exc}")
        log(f"  ok {md.relative_to(dest)}")


def build_index_readme(resume: bool, force: bool) -> None:
    index_dir = ROOT_PT / "college-projects-pt"
    index_dir.mkdir(parents=True, exist_ok=True)
    src_readme = COLLEGE_PROJECTS / "README.md"
    dest_readme = index_dir / "README.md"
    if not src_readme.exists():
        return
    en = src_readme.read_text(encoding="utf-8")
    if not resume or force or not dest_readme.exists():
        header = (
            "# Projetos universitários — EMU (português)\n\n"
            "> Índice em português dos repositórios de trabalhos da graduação. "
            "Cada pasta `… (PT)` espelha um curso; veja `LEIA-ME.md` em cada uma.\n\n"
        )
        dest_readme.write_text(header + translate_markdown(en), encoding="utf-8")
        log("wrote college-projects-pt/README.md")
    shutil.copy2(Path(__file__), index_dir / "build_portuguese_mirrors.py")
    (index_dir / ".mirror-source.json").write_text(
        json.dumps({"source": "college-projects", "language": "pt-BR"}, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", action="append")
    parser.add_argument("--resume", action="store_true", help="Do not wipe existing PT mirror")
    parser.add_argument("--force", action="store_true", help="Re-translate all markdown")
    parser.add_argument("--skip-index", action="store_true")
    args = parser.parse_args()

    names = args.repo or REPOS
    ROOT_PT.mkdir(parents=True, exist_ok=True)
    for name in names:
        mirror_repo(name, args.resume, args.force)
    if not args.skip_index:
        build_index_readme(args.resume, args.force)
    log(f"Done. PT mirrors: {ROOT_PT}")


if __name__ == "__main__":
    main()
