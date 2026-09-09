"""Render the maintained Week 3 Markdown source as a single PDF (requires reportlab)."""

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/week3-report.md"
OUTPUT = ROOT / "output/pdf/Orbit_Week3_Report.pdf"
WIDTH = 504


class Burndown(Flowable):
    """Only September 7-8 observed values; never extend actuals into the future."""

    def __init__(self):
        super().__init__()
        self.width, self.height = WIDTH, 160

    def draw(self):
        c = self.canv
        left, bottom, plot_w, plot_h = 40, 38, 450, 100
        cutoff = left + plot_w / 20
        c.setFillColor(colors.HexColor("#f3f4f6"))
        c.rect(cutoff, bottom, plot_w * 19 / 20, plot_h, stroke=0, fill=1)
        c.setFont("Helvetica", 8)
        for val in (0, 5, 10, 15, 20):
            y = bottom + val / 20 * plot_h
            c.setStrokeColor(colors.HexColor("#d1d5db"))
            c.line(left, y, left + plot_w, y)
            c.setFillColor(colors.black)
            c.drawRightString(left - 7, y - 3, str(val))
        c.setStrokeColor(colors.black)
        c.line(left, bottom, left, bottom + plot_h)
        c.line(left, bottom, left + plot_w, bottom)
        c.setDash(4, 3)
        c.setStrokeColor(colors.HexColor("#777777"))
        c.line(left, bottom + plot_h, left + plot_w, bottom)
        c.setDash()
        c.setStrokeColor(colors.HexColor("#185b78"))
        c.setFillColor(colors.HexColor("#185b78"))
        c.setLineWidth(2.5)
        c.line(left, bottom, cutoff, bottom)
        for x in (left, cutoff):
            c.circle(x, bottom, 3, stroke=0, fill=1)
        c.setFillColor(colors.black)
        c.setLineWidth(1)
        for offset, label in (
            (0, "Sep 7"),
            (6, "Sep 13"),
            (13, "Sep 20"),
            (20, "Sep 27"),
        ):
            c.drawCentredString(left + plot_w * offset / 20, bottom - 14, label)
        c.drawCentredString(
            left + plot_w / 2, bottom - 28, "Sprint calendar date (2026)"
        )
        c.saveState()
        c.translate(11, bottom + plot_h / 2)
        c.rotate(90)
        c.drawCentredString(0, 0, "Open-issue points remaining")
        c.restoreState()
        c.setFont("Helvetica-Bold", 8)
        c.drawString(left, 152, "Observed issue status (Sep 7-8): 0 points")
        c.setFont("Helvetica", 8)
        c.drawRightString(left + plot_w, 152, "Dashed: original-plan linear reference")
        c.setFillColor(colors.HexColor("#555555"))
        c.drawString(
            cutoff + 12,
            bottom + plot_h - 13,
            "After Sep 8: no actual observations plotted",
        )


def inline(text):
    value = html.escape(text, quote=False)
    value = re.sub(
        r"\[([^\]]+)\]\((https?://[^)]+)\)",
        r'<link href="\2" color="#185b78"><u>\1</u></link>',
        value,
    )
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    return re.sub(r"`([^`]+)`", r'<font name="Courier" size="8">\1</font>', value)


def footer(c, doc):
    c.saveState()
    c.setStrokeColor(colors.HexColor("#cccccc"))
    c.line(54, 39, 558, 39)
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(
        54, 26, "Orbit | SWENG 894 | Week 3 | Evidence through Sep 8, 2026 (PDT)"
    )
    c.drawRightString(558, 26, str(doc.page))
    c.restoreState()


def build():
    # Embed locally available Arial for stable rendering without font substitution.
    # On other platforms ReportLab's standard PDF fonts remain the fallback.
    font_dir = Path("/System/Library/Fonts/Supplemental")
    if (font_dir / "Arial.ttf").exists():
        pdfmetrics.registerFont(TTFont("Helvetica", str(font_dir / "Arial.ttf")))
        pdfmetrics.registerFont(
            TTFont("Helvetica-Bold", str(font_dir / "Arial Bold.ttf"))
        )
        pdfmetrics.registerFontFamily(
            "Helvetica", normal="Helvetica", bold="Helvetica-Bold"
        )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=9.5, leading=12.7, spaceAfter=7
        )
    )
    styles.add(
        ParagraphStyle(
            "Cell", parent=styles["Body"], fontSize=8.5, leading=10.8, spaceAfter=0
        )
    )
    styles.add(
        ParagraphStyle(
            "BulletCustom",
            parent=styles["Body"],
            leftIndent=10,
            firstLineIndent=-8,
            spaceAfter=5,
        )
    )
    for name, size, leading in (
        ("Heading1", 22, 27),
        ("Heading2", 15, 19),
        ("Heading3", 10.5, 14),
    ):
        styles[name].fontName = "Helvetica-Bold"
        styles[name].fontSize = size
        styles[name].leading = leading
        styles[name].textColor = colors.black
        styles[name].spaceBefore = 9
        styles[name].spaceAfter = 7
    flow = []
    lines = SOURCE.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == "<!-- pagebreak -->":
            flow.append(PageBreak())
        elif line == "<!-- burndown -->":
            flow.extend([Burndown(), Spacer(1, 7)])
        elif line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [s.strip() for s in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", s) for s in cells):
                    rows.append(cells)
                i += 1
            if len(rows[0]) == 5:
                widths = [58, 240, 62, 63, 81]
            elif len(rows[0]) == 4:
                widths = [52, 38, 99, 315]
            elif rows[0][0] == "Date":
                widths = [47, 143, 314]
            else:
                widths = [100, 50, 354]
            data = [
                [
                    Paragraph(inline(f"**{v}**" if n == 0 else v), styles["Cell"])
                    for v in row
                ]
                for n, row in enumerate(rows)
            ]
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf1f3")),
                        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#6b7280")),
                        (
                            "LINEBELOW",
                            (0, 1),
                            (-1, -1),
                            0.25,
                            colors.HexColor("#d1d5db"),
                        ),
                        ("LEFTPADDING", (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ]
                )
            )
            flow.extend([table, Spacer(1, 8)])
            continue
        elif line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            flow.append(
                Paragraph(
                    inline(line[level:].strip()), styles[f"Heading{min(level, 3)}"]
                )
            )
        elif line.startswith("- ") or re.match(r"^\d+\. ", line):
            flow.append(Paragraph(inline(line), styles["BulletCustom"]))
        else:
            para = [line]
            while (
                i + 1 < len(lines)
                and lines[i + 1].strip()
                and not lines[i + 1].lstrip().startswith(("#", "|", "<!--", "- "))
            ):
                i += 1
                para.append(lines[i].strip())
            flow.append(Paragraph(inline(" ".join(para)), styles["Body"]))
        i += 1
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=43,
        bottomMargin=51,
        title="Orbit - Week 3 Progress Report I",
        author="Andrew Lam",
    )
    doc.build(flow, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    build()
