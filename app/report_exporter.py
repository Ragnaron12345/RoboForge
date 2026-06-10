from __future__ import annotations

import os
import re
import textwrap
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer

from app.card_tools import ensure_card_format
from app.text_cleanup import cleanup_markdown

SECTION_FILES = [
    ("Projektspezifikation", "project_spec.md"),
    ("Projektübersicht", "README.md"),
    ("Komponenten", "components.md"),
    ("Verdrahtung", "wiring.md"),
    ("Wokwi-Schaltungsprofil", "wokwi/circuit_profile.json"),
    ("Code-Skelett", "code.ino"),
    ("Druckteileliste", "printable_parts.md"),
    ("3D-Druckvorlage", "model.scad"),
]

_CODE_PREFIXES = (
    "const ", "void ", "module ", "translate", "difference", "cube", "cylinder",
    "union", "hull", "for (", "if (", "else", "//", "#include", "{", "}", "[", "]",
)


def _find_font() -> str | None:
    explicit = os.getenv("ROBOFORGE_PDF_FONT")
    candidates = [explicit] if explicit else []
    candidates += [
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/tahoma.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for item in candidates:
        if item and Path(item).exists():
            return item
    return None


def _font_name() -> str:
    font_path = _find_font()
    if font_path:
        try:
            pdfmetrics.registerFont(TTFont("RoboForgeSans", font_path))
            return "RoboForgeSans"
        except Exception:
            pass
    return "Helvetica"


def _read(project_dir: Path, name: str) -> str:
    path = project_dir / name
    if not path.exists():
        return f"Hinweis: {name} wurde noch nicht erstellt."
    text = path.read_text(encoding="utf-8")
    if name in {"components.md", "wiring.md"}:
        text = ensure_card_format(text)
    return cleanup_markdown(text)


def build_report_markdown(project_dir: Path, title: str, description: str) -> str:
    parts = [
        f"# RoboForge Bericht: {title}",
        "",
        f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        "",
        "Dieser Bericht ist eine Lern- und Entwurfsvorlage. Er ersetzt keine technische Prüfung.",
        "",
        "## Kurzbeschreibung",
        description or "Keine Beschreibung angegeben.",
    ]
    for heading, filename in SECTION_FILES:
        parts += ["", f"# {heading}", "", _read(project_dir, filename)]
    parts += [
        "",
        "# Abschließende Prüfliste",
        "",
        "- Pinout des konkreten Controllers prüfen.",
        "- Spannungen, Ströme und gemeinsame Masse prüfen.",
        "- Datenblätter der Bauteile lesen.",
        "- 3D-Maße vor dem Druck mit realen Komponenten vergleichen.",
        "- Wokwi-Schaltplan als Lernvorlage behandeln, nicht als Produktionsschaltplan.",
    ]
    report = "\n".join(parts).strip() + "\n"
    (project_dir / "report.md").write_text(report, encoding="utf-8")
    return report


def _styles():
    font = _font_name()
    base = getSampleStyleSheet()
    common = {"fontName": font, "splitLongWords": 1, "wordWrap": "LTR"}
    return {
        "title": ParagraphStyle("title", parent=base["Title"], **common, fontSize=22, leading=27, spaceAfter=12),
        "h1": ParagraphStyle("h1", parent=base["Heading1"], **common, fontSize=16, leading=20, spaceBefore=7, spaceAfter=7),
        "h2": ParagraphStyle("h2", parent=base["Heading2"], **common, fontSize=12.5, leading=16, spaceBefore=6, spaceAfter=4),
        "body": ParagraphStyle("body", parent=base["BodyText"], **common, fontSize=9.6, leading=13, spaceAfter=4.5),
        "bullet": ParagraphStyle("bullet", parent=base["BodyText"], **common, fontSize=9.6, leading=13, leftIndent=9, firstLineIndent=-9, spaceAfter=3.5),
        "code": ParagraphStyle("code", fontName=font, fontSize=6.8, leading=8.2, textColor=colors.HexColor("#222222"), backColor=colors.HexColor("#F5F5F5"), borderPadding=4, splitLongWords=1),
        "small": ParagraphStyle("small", parent=base["BodyText"], **common, fontSize=8.2, leading=10.5, textColor=colors.HexColor("#666666")),
    }


def _clean_inline(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^>\s*", "Hinweis: ", text)
    text = text.replace("**", "").replace("__", "").replace("*", "")
    text = text.replace("`", "")
    return text


def _wrap_code(text: str, width: int = 86, max_lines: int = 240) -> str:
    wrapped: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()
        if not line:
            wrapped.append("")
            continue
        indent_len = len(line) - len(line.lstrip(" "))
        indent = " " * min(indent_len, 10)
        chunks = textwrap.wrap(
            line,
            width=width,
            subsequent_indent=indent + "  ",
            break_long_words=True,
            break_on_hyphens=False,
            replace_whitespace=False,
            drop_whitespace=False,
        )
        wrapped.extend(chunks or [line])
        if len(wrapped) >= max_lines:
            wrapped.append("... gekürzt ...")
            break
    return "\n".join(wrapped)


def _add_code(flow: list, code: str, styles: dict) -> None:
    if code.strip():
        flow.append(Preformatted(_wrap_code(code), styles["code"], maxLineLength=90))
        flow.append(Spacer(1, 4))


def _looks_like_code(stripped: str) -> bool:
    if stripped.startswith(_CODE_PREFIXES):
        return True
    if re.match(r'^[\s"\w.-]+[:=]\s*[\[{"\w.-]', stripped) and any(ch in stripped for ch in "{}[];"):
        return True
    return False


def _markdown_to_flowables(md: str, styles: dict) -> list:
    flow: list = []
    in_code = False
    code_lines: list[str] = []
    loose_code: list[str] = []

    def flush_loose_code() -> None:
        nonlocal loose_code
        if loose_code:
            _add_code(flow, "\n".join(loose_code), styles)
            loose_code = []

    for line in md.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            flush_loose_code()
            if in_code:
                _add_code(flow, "\n".join(code_lines), styles)
                code_lines = []
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if stripped in {"---", "***", "___"}:
            flush_loose_code()
            flow.append(Spacer(1, 5))
            continue

        if _looks_like_code(stripped):
            loose_code.append(line)
            continue

        flush_loose_code()
        if not stripped:
            flow.append(Spacer(1, 3))
        elif stripped.startswith("# "):
            flow.append(Paragraph(escape(_clean_inline(stripped[2:])), styles["h1"]))
        elif stripped.startswith("## "):
            flow.append(Paragraph(escape(_clean_inline(stripped[3:])), styles["h2"]))
        elif stripped.startswith("### "):
            flow.append(Paragraph(escape(_clean_inline(stripped[4:])), styles["h2"]))
        elif stripped.startswith(('- ', '* ', '• ')):
            item = stripped[2:] if stripped[:2] in {'- ', '* '} else stripped[2:]
            flow.append(Paragraph("• " + escape(_clean_inline(item)), styles["bullet"]))
        elif re.match(r"^\d+[.)]\s+", stripped):
            flow.append(Paragraph(escape(_clean_inline(stripped)), styles["bullet"]))
        else:
            flow.append(Paragraph(escape(_clean_inline(stripped)), styles["body"]))

    if in_code and code_lines:
        _add_code(flow, "\n".join(code_lines), styles)
    flush_loose_code()
    return flow


def _footer(canvas, doc):
    canvas.saveState()
    font = _font_name()
    canvas.setFont(font, 7)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawRightString(A4[0] - 18 * mm, 8 * mm, f"Seite {doc.page}")
    canvas.restoreState()


def export_report_pdf(project_dir: Path, title: str, description: str) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    try:
        build_report_markdown(project_dir, title, description)
        pdf_path = project_dir / "report.pdf"
        styles = _styles()
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=18 * mm,
            bottomMargin=16 * mm,
        )
        story: list = [
            Paragraph("robo forge Bericht", styles["title"]),
            Paragraph(escape(title), styles["h1"]),
            Paragraph(escape(description or "Deutschsprachiges Projekt"), styles["body"]),
            Spacer(1, 8),
            Paragraph("Dokumentation, Komponenten, Verdrahtung, Code, 3D-Modell und Prüfliste.", styles["small"]),
            PageBreak(),
        ]
        for heading, filename in SECTION_FILES:
            story.append(Paragraph(heading, styles["h1"]))
            text = _read(project_dir, filename)
            story.extend(_markdown_to_flowables(text, styles))
            story.append(PageBreak())
        story.append(Paragraph("Abschließende Prüfliste", styles["h1"]))
        checklist = """- Pinout des konkreten Boards prüfen.
- Spannungen, Ströme, Akku und gemeinsame Masse prüfen.
- Wokwi diagram.json als Lernvorlage behandeln.
- OpenSCAD-Datei vor dem Druck mit realen Bauteilmaßen abgleichen.
- Code-Skelett vor echter Hardware anpassen und testen."""
        story.extend(_markdown_to_flowables(checklist, styles))
        doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
        return ["report.md", "report.pdf"], warnings
    except Exception as error:
        warnings.append(f"PDF-Bericht konnte nicht erstellt werden: {error}")
        return [], warnings
