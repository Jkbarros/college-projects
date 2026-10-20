#!/usr/bin/env python3
"""Regenerate docs/demo.gif for a (PT) course folder with Portuguese labels."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 720, 200
BG = (15, 23, 42)
PANEL = (30, 41, 59)
TEXT = (226, 232, 240)
ACCENT = (56, 189, 248)

# (header, [(title, body), ...]) per English source folder name
PT_DEMOS: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "CET 151 - Intro to Computing in Engineering Tech": (
        "CET 151 — Ferramentas de engenharia",
        [
            ("MATLAB", "Unidade 7 — gráficos e estatística"),
            ("Excel", "Projetos e macros"),
            ("C++", "Fundamentos e menus"),
        ],
    ),
    "COSC 111 - Programming and Data Structures": (
        "COSC 111 — Estruturas de dados",
        [
            ("Tabela hash", "Implementação em Java"),
            ("Herança", "Laboratório OOP"),
            ("JavaFX", "Projeto tabuleiro"),
        ],
    ),
    "COSC 314 - Computational Discrete Structs": (
        "COSC 314 — Estruturas discretas",
        [
            ("Relações", "Projeto 1 — matrizes"),
            ("Dijkstra", "Caminhos mínimos"),
            ("Grafos", "Implementação Java"),
        ],
    ),
    "COSC 381 - Software Engineering Solutions": (
        "COSC 381 — Engenharia de software",
        [
            ("Git", "Modelo de dados e fluxo"),
            ("Linux", "Shell e exercícios"),
            ("AWS Academy", "Laboratórios na nuvem"),
        ],
    ),
    "Cyber Crime Investigation": (
        "Investigação de crimes cibernéticos — caso PSN",
        [
            ("Introdução", "Contexto do vazamento"),
            ("Marcos", "Linha do tempo e impacto"),
            ("Mitigação", "Lacunas de controle"),
            ("Final", "Relatório de investigação"),
        ],
    ),
    "IA 103 - Information Security Overview": (
        "IA 103 — Visão geral de segurança",
        [
            ("Arquivo", "Calculando SHA-256"),
            ("Digest", "Consulta VirusTotal"),
            ("Consenso", "Um sinal, não prova"),
        ],
    ),
    "IA 244 - Administration of Computer Systems": (
        "IA 244 — Administração de sistemas",
        [
            ("Domínio", "DC1 e DC2 implantados"),
            ("Cliente", "ipconfig e ping"),
            ("Lab 4", "Capturas de administração"),
            ("Prova", "Exame prático"),
        ],
    ),
    "IA 329 - Policy Development Info Assurance": (
        "IA 329 — Políticas de segurança",
        [
            ("Política", "Rascunhos e revisão"),
            ("DR", "Modelo de plano"),
            ("Pesquisa", "Bibliografia anotada"),
            ("Tema", "Casa inteligente"),
        ],
    ),
    "IA 385 - Database Web Application Security": (
        "IA 385 — Segurança de banco e web",
        [
            ("MySQL", "Labs de instalação"),
            ("SQL Server", "Atribuição 3"),
            ("Oracle", "Atribuição 4"),
            ("Hardening", "Usuários e SQL"),
        ],
    ),
    "IA 403 - Malware Analysis Reverse Engineering": (
        "IA 403 — Análise de malware",
        [
            ("Estática", "strings e PE"),
            ("Disassembly", "saltos e procedimentos"),
            ("Tarefas", "Atribuições II e III"),
            ("Relatório", "Análise final"),
        ],
    ),
    "IA 445 - Ethical Hacking Offensive Security": (
        "IA 445 — Hacking ético",
        [
            ("Módulos", "Curso EHE + Earth"),
            ("Labs", "Ataques e contramedidas"),
            ("Mobile / IoT", "Labs 09–10"),
            ("Infra", "Script VirtualBox"),
        ],
    ),
    "IA 447 - Digital Forensics I": (
        "IA 447 — Forense digital I",
        [
            ("Evidência", "Padrão Daubert"),
            ("Host", "Windows, registro, memória"),
            ("Arquivos", "EXIF e esteganografia"),
            ("Casos", "Cenários de laboratório"),
        ],
    ),
    "IA455 - Incident Response": (
        "IA 455 — Resposta a incidentes",
        [
            ("Preparar", "Lab virtual + sensores"),
            ("Detectar", "Logs e PCAP"),
            ("Analisar", "Memória e disco"),
            ("Recuperar", "Restaurar e endurecer"),
        ],
    ),
}

DEFAULT = (
    "Portfólio acadêmico — EMU",
    [
        ("Documentação", "Notas em markdown"),
        ("Archive", "Envios originais Canvas"),
        ("Scripts", "Utilitários do curso"),
    ],
)


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("segoeui.ttf", "arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def panel_frame(header: str, title: str, body: str) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((24, 24, W - 24, H - 24), radius=12, fill=PANEL)
    draw.text((40, 28), header, fill=ACCENT, font=load_font(18))
    draw.text((40, 62), title, fill=TEXT, font=load_font(22))
    draw.text((40, 100), body, fill=TEXT, font=load_font(15))
    return img


def step_frame(header: str, steps: list[tuple[str, str]], active: int) -> Image.Image:
    img = Image.new("RGB", (W, H), (18, 22, 32))
    draw = ImageDraw.Draw(img)
    draw.text((24, 16), header, fill=TEXT, font=load_font(20))
    box_w = min(150, (W - 48 - 10 * (len(steps) - 1)) // max(len(steps), 1))
    gap = 10
    y = 72
    for i, (name, sub) in enumerate(steps):
        x = 24 + i * (box_w + gap)
        fill = ACCENT if i == active else (40, 48, 66)
        draw.rounded_rectangle((x, y, x + box_w, y + 56), radius=8, fill=fill, outline=ACCENT, width=2)
        tf = load_font(13)
        draw.text((x + 8, y + 10), name[:18], fill=(15, 23, 42) if i == active else TEXT, font=tf)
        draw.text((x + 8, y + 32), sub[:22], fill=(15, 23, 42) if i == active else TEXT, font=load_font(10))
    return img


def main() -> None:
    repo = Path(sys.argv[1]).resolve()
    meta_path = repo / ".mirror-source.json"
    source = ""
    if meta_path.exists():
        source = json.loads(meta_path.read_text(encoding="utf-8")).get("source", "")
    header, frames = PT_DEMOS.get(source, DEFAULT)
    out = repo / "docs" / "demo.gif"
    out.parent.mkdir(parents=True, exist_ok=True)

    if len(frames) >= 4 and source in (
        "Cyber Crime Investigation",
        "IA455 - Incident Response",
    ):
        images = [step_frame(header, frames, i) for i in range(len(frames))]
    else:
        images = [panel_frame(header, t, b) for t, b in frames]

    images[0].save(out, save_all=True, append_images=images[1:], duration=900, loop=0, optimize=True)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
