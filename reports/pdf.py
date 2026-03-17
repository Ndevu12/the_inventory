"""PDF export utilities for reports.

Provides a mixin for class-based views and a standalone helper for
generating PDF responses from tabular data using ReportLab.
"""

import io
from datetime import date, datetime
from decimal import Decimal

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


_styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    parent=_styles["Heading1"],
    fontSize=16,
    spaceAfter=6 * mm,
)

SUBTITLE_STYLE = ParagraphStyle(
    "ReportSubtitle",
    parent=_styles["Normal"],
    fontSize=10,
    textColor=colors.grey,
    spaceAfter=4 * mm,
)

HEADER_BG = colors.HexColor("#1F2937")
HEADER_FG = colors.white
ALT_ROW_BG = colors.HexColor("#F9FAFB")
GRID_COLOR = colors.HexColor("#E5E7EB")


def _format_cell(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


def export_pdf(
    *,
    filename: str,
    title: str,
    headers: list[str],
    rows: list[list],
    subtitle: str = "",
    orientation: str = "landscape",
) -> HttpResponse:
    """Build an ``HttpResponse`` containing a styled PDF report.

    Parameters
    ----------
    filename : str
        Download filename (e.g. ``"stock_valuation.pdf"``).
    title : str
        Report title rendered at the top of the first page.
    headers : list[str]
        Column header labels.
    rows : list[list]
        Each inner list is one row of cell values.
    subtitle : str
        Optional line below the title (e.g. filter summary).
    orientation : str
        ``"landscape"`` (default) or ``"portrait"``.
    """
    buf = io.BytesIO()
    pagesize = landscape(A4) if orientation == "landscape" else A4

    doc = SimpleDocTemplate(
        buf,
        pagesize=pagesize,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    elements = []

    elements.append(Paragraph(title, TITLE_STYLE))
    if subtitle:
        elements.append(Paragraph(subtitle, SUBTITLE_STYLE))

    generated = f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    elements.append(Paragraph(generated, SUBTITLE_STYLE))
    elements.append(Spacer(1, 4 * mm))

    table_data = [headers]
    for row in rows:
        table_data.append([_format_cell(cell) for cell in row])

    col_count = len(headers)
    available_width = pagesize[0] - 30 * mm
    col_width = available_width / col_count

    table = Table(table_data, colWidths=[col_width] * col_count, repeatRows=1)

    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
        ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.5, GRID_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]

    for i in range(1, len(table_data)):
        if i % 2 == 0:
            style_commands.append(
                ("BACKGROUND", (0, i), (-1, i), ALT_ROW_BG)
            )

    table.setStyle(TableStyle(style_commands))
    elements.append(table)

    doc.build(elements)

    response = HttpResponse(buf.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


class PDFExportMixin:
    """Mixin for Django CBVs that adds ``?export=pdf`` support.

    Subclasses must implement :meth:`get_pdf_data` returning
    ``(filename, title, headers, rows)`` and optionally a subtitle.
    """

    def get(self, request, *args, **kwargs):
        if request.GET.get("export") == "pdf":
            data = self.get_pdf_data()
            if len(data) == 5:
                filename, title, headers, rows, subtitle = data
            else:
                filename, title, headers, rows = data
                subtitle = ""
            return export_pdf(
                filename=filename,
                title=title,
                headers=headers,
                rows=rows,
                subtitle=subtitle,
            )
        return super().get(request, *args, **kwargs)

    def get_pdf_data(self) -> tuple:
        """Return ``(filename, title, headers, rows[, subtitle])``."""
        raise NotImplementedError
