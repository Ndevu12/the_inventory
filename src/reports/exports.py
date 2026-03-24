"""CSV export utilities for reports.

Provides a mixin for class-based views and a standalone helper for
generating CSV responses from tabular data.
"""

import csv
from datetime import date, datetime
from decimal import Decimal

from django.http import HttpResponse


def export_csv(*, filename: str, headers: list[str], rows: list[list]) -> HttpResponse:
    """Build an ``HttpResponse`` containing a CSV file.

    Parameters
    ----------
    filename : str
        The download filename (e.g. ``"stock_valuation.csv"``).
    headers : list[str]
        Column header labels.
    rows : list[list]
        Each inner list is one row of cell values.
    """
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_format_cell(cell) for cell in row])
    return response


def _format_cell(value):
    """Coerce report values to CSV-friendly strings."""
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return str(value.quantize(Decimal("0.01")))
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(value, date):
        return value.strftime("%Y-%m-%d")
    return str(value)


class ExportMixin:
    """Mixin for Django CBVs that adds ``?export=csv`` and ``?export=pdf``.

    Subclasses must implement :meth:`get_csv_data` returning
    ``(filename, headers, rows)`` and :meth:`get_pdf_data` returning
    ``(filename, title, headers, rows[, subtitle])``.
    """

    def get(self, request, *args, **kwargs):
        export_format = request.GET.get("export")
        if export_format == "csv":
            filename, headers, rows = self.get_csv_data()
            return export_csv(filename=filename, headers=headers, rows=rows)
        if export_format == "pdf":
            from reports.pdf import export_pdf

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

    def get_csv_data(self) -> tuple[str, list[str], list[list]]:
        """Return ``(filename, headers, rows)`` for CSV export."""
        raise NotImplementedError

    def get_pdf_data(self) -> tuple:
        """Return ``(filename, title, headers, rows[, subtitle])`` for PDF export."""
        raise NotImplementedError


# Backwards-compatible alias
CSVExportMixin = ExportMixin
