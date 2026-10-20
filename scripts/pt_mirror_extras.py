#!/usr/bin/env python3
"""
Optional PT mirror extras (run after or alongside build_portuguese_mirrors.py):

1. Ensure all course (PT) folders exist (sync from English repos)
2. Translate archive/canvas-submissions DOCX & PDF -> docs/canvas-pt/*.md
3. Regenerate docs/demo.gif with Portuguese labels
4. Remove *.md.en.bak under College Projects PT

  pip install -r scripts/requirements-pt-mirror.txt
  python scripts/pt_mirror_extras.py
  python scripts/pt_mirror_extras.py --skip-archive   # GIFs + cleanup only
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT_EN = Path(__file__).resolve().parents[2]
ROOT_PT = ROOT_EN.parent / "College Projects PT"
SCRIPT_DIR = Path(__file__).resolve().parent

# Import translator helpers from sibling module
sys.path.insert(0, str(SCRIPT_DIR))
from build_portuguese_mirrors import (  # noqa: E402
    REPOS,
    SKIP_DIR_NAMES,
    log,
    sync_tree,
    translate_markdown,
    translate_plain,
)

try:
    from docx import Document
    from pypdf import PdfReader
except ImportError:
    Document = None  # type: ignore
    PdfReader = None  # type: ignore


def slugify(stem: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-")
    return s[:96] or "export"


def ensure_pt_folders() -> None:
    for name in REPOS:
        src = ROOT_EN / name
        dest = ROOT_PT / f"{name} (PT)"
        if not src.is_dir():
            continue
        if not dest.exists():
            log(f"creating mirror {dest.name}")
            shutil.copytree(
                src,
                dest,
                ignore=shutil.ignore_patterns(*SKIP_DIR_NAMES),
                dirs_exist_ok=True,
            )
        else:
            sync_tree(src, dest)
        meta = {"source": name, "language": "pt-BR"}
        (dest / ".mirror-source.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")


def docx_to_md_text(path: Path) -> str:
    doc = Document(path)
    lines: list[str] = [f"# {path.stem}", ""]
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            lines.append(t)
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def pdf_to_md_text(path: Path) -> str:
    reader = PdfReader(path)
    lines = [f"# {path.stem}", ""]
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            lines.extend([f"## Página {i}", "", text, ""])
    return "\n".join(lines).strip() + "\n"


def translate_archive_repo(repo_pt: Path, force: bool) -> None:
    if Document is None or PdfReader is None:
        log("install python-docx and pypdf for archive translation")
        return
    archive = repo_pt / "archive" / "canvas-submissions"
    if not archive.is_dir():
        return
    out_dir = repo_pt / "docs" / "canvas-pt"
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog: list[str] = [
        "# Exportações Canvas (PT-BR)",
        "",
        "Tradução automática dos envios em `archive/canvas-submissions/`. "
        "PDFs/DOCX originais permanecem em inglês no `archive/`.",
        "",
        "| Arquivo | Markdown (PT) |",
        "|---------|----------------|",
    ]
    for f in sorted(archive.iterdir()):
        if not f.is_file():
            continue
        rel_arc = f.relative_to(repo_pt).as_posix().replace(" ", "%20")
        slug = slugify(f.stem) + ".md"
        dest = out_dir / slug
        if dest.exists() and not force:
            catalog.append(f"| [{f.name}](../{rel_arc}) | [{slug}]({slug}) |")
            continue
        try:
            if f.suffix.lower() == ".docx":
                body = docx_to_md_text(f)
            elif f.suffix.lower() == ".pdf":
                body = pdf_to_md_text(f)
            elif f.suffix.lower() == ".doc":
                body = (
                    f"# {f.stem}\n\n"
                    f"**Arquivo:** [`{f.name}`](../{rel_arc})\n\n"
                    "Formato `.doc` legado — abra o arquivo no `archive/` localmente. "
                    "Conteúdo não extraído automaticamente.\n"
                )
            else:
                continue
            header = (
                f"**Origem:** [`{f.name}`](../{rel_arc})  \n"
                "**Idioma:** tradução automática PT-BR\n\n"
            )
            dest.write_text(header + translate_markdown(body), encoding="utf-8")
            catalog.append(f"| [{f.name}](../{rel_arc}) | [{slug}]({slug}) |")
            log(f"  archive-pt {repo_pt.name}/{slug}")
            time.sleep(0.2)
        except Exception as exc:
            log(f"  WARN archive {f.name}: {exc}")
    (out_dir / "README.md").write_text("\n".join(catalog) + "\n", encoding="utf-8")


def remove_en_bak() -> int:
    n = 0
    for bak in ROOT_PT.rglob("*.md.en.bak"):
        bak.unlink()
        n += 1
    return n


def regenerate_pt_demo(repo_pt: Path) -> None:
    script = SCRIPT_DIR / "regenerate_pt_demo.py"
    if not script.exists():
        return
    subprocess.run(
        [sys.executable, str(script), str(repo_pt)],
        check=False,
        cwd=str(SCRIPT_DIR),
    )


def update_leia_me(repo_pt: Path) -> None:
    name = json.loads((repo_pt / ".mirror-source.json").read_text(encoding="utf-8")).get("source", "")
    (repo_pt / "LEIA-ME.md").write_text(
        "# Versão em português (PT-BR)\n\n"
        "Espelho do repositório em inglês com:\n\n"
        "- `*.md` traduzidos automaticamente\n"
        "- `docs/canvas-pt/` — DOCX/PDF do Canvas traduzidos\n"
        "- `docs/demo.gif` — animação do README em português\n\n"
        f"**Origem:** `{name}`\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-archive", action="store_true")
    parser.add_argument("--skip-gifs", action="store_true")
    parser.add_argument("--skip-cleanup", action="store_true")
    parser.add_argument("--force-archive", action="store_true")
    args = parser.parse_args()

    ROOT_PT.mkdir(parents=True, exist_ok=True)
    ensure_pt_folders()

    if not args.skip_archive:
        for name in REPOS:
            repo_pt = ROOT_PT / f"{name} (PT)"
            if repo_pt.is_dir():
                log(f"=== archive PT: {name} ===")
                translate_archive_repo(repo_pt, args.force_archive)

    if not args.skip_gifs:
        for name in REPOS:
            repo_pt = ROOT_PT / f"{name} (PT)"
            if repo_pt.is_dir():
                log(f"=== demo PT: {name} ===")
                regenerate_pt_demo(repo_pt)
                update_leia_me(repo_pt)

    if not args.skip_cleanup:
        removed = remove_en_bak()
        log(f"removed {removed} *.md.en.bak files")

    log(f"extras done -> {ROOT_PT}")


if __name__ == "__main__":
    main()
