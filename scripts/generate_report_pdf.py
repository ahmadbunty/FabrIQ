"""
Generate FabrIQ_Technical_Report.pdf from docs/FabrIQ_Technical_Report.md

Usage:
  cd scripts
  pip install -r requirements-report.txt
  python generate_report_pdf.py

Output:
  ../docs/FabrIQ_Technical_Report.pdf
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    PageBreak,
)

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "docs" / "FabrIQ_Technical_Report.md"
PDF_PATH = ROOT / "docs" / "FabrIQ_Technical_Report.pdf"


def md_inline_to_xml(text: str) -> str:
    """Convert **bold** to XML for ReportLab Paragraph; escape HTML."""
    text = html.escape(text.strip())
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|") and "|" in line.strip()[1:]


def parse_markdown(md_text: str) -> list:
    """Return list of (type, content) where type in title,h1,h2,h3,p,table,rule."""
    blocks: list[tuple[str, str]] = []
    lines = md_text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip() == "---":
            blocks.append(("rule", ""))
            i += 1
            continue
        if line.startswith("# ") and not line.startswith("## "):
            blocks.append(("title", line[2:].strip()))
            i += 1
            continue
        if line.startswith("## ") and not line.startswith("### "):
            blocks.append(("h1", line[3:].strip()))
            i += 1
            continue
        if line.startswith("### "):
            blocks.append(("h2", line[4:].strip()))
            i += 1
            continue
        if is_table_row(line):
            rows = []
            while i < len(lines) and is_table_row(lines[i]):
                rows.append(lines[i].strip())
                i += 1
            blocks.append(("table", "\n".join(rows)))
            continue
        if line.strip() == "":
            i += 1
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() != "":
            if lines[i].startswith("#") or lines[i].strip() == "---":
                break
            if is_table_row(lines[i]):
                break
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            blocks.append(("p", " ".join(para_lines)))
        continue
    return blocks


def build_pdf(blocks: list[tuple[str, str]]) -> None:
    PDF_PATH.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="Justify",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
            fontSize=10,
            leading=14,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TitleDoc",
            parent=styles["Title"],
            fontSize=18,
            leading=22,
            spaceAfter=14,
            textColor=colors.HexColor("#1565c0"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H1Doc",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#0d47a1"),
        )
    )
    styles.add(
        ParagraphStyle(
            name="H2Doc",
            parent=styles["Heading2"],
            fontSize=11,
            leading=14,
            spaceBefore=8,
            spaceAfter=6,
        )
    )

    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="FabrIQ Technical Report",
        author="FabrIQ Project",
    )

    story = []

    for kind, content in blocks:
        if kind == "rule":
            story.append(Spacer(1, 6))
            continue
        if kind == "title":
            story.append(Paragraph(md_inline_to_xml(content), styles["TitleDoc"]))
            story.append(Spacer(1, 12))
            continue
        if kind == "h1":
            story.append(Paragraph(md_inline_to_xml(content), styles["H1Doc"]))
            continue
        if kind == "h2":
            story.append(Paragraph(md_inline_to_xml(content), styles["H2Doc"]))
            continue
        if kind == "table":
            mono = html.escape(content)
            story.append(
                Paragraph(f"<font face='Courier' size='8'>{mono.replace(chr(10), '<br/>')}</font>", styles["Justify"])
            )
            story.append(Spacer(1, 8))
            continue
        if kind == "p":
            story.append(Paragraph(md_inline_to_xml(content), styles["Justify"]))

    doc.build(story)


def main() -> None:
    if not MD_PATH.exists():
        raise SystemExit(f"Missing markdown report: {MD_PATH}")
    md_text = MD_PATH.read_text(encoding="utf-8")
    blocks = parse_markdown(md_text)
    build_pdf(blocks)
    print(f"Wrote PDF: {PDF_PATH}")


if __name__ == "__main__":
    main()
