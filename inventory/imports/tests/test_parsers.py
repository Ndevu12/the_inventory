"""Tests for CSV and Excel file parsing utilities."""

from io import BytesIO, StringIO

from django.test import TestCase
from openpyxl import Workbook

from inventory.imports.parsers import parse_csv, parse_excel


class ParseCsvTests(TestCase):
    """Tests for ``parse_csv``."""

    def test_parse_csv_basic(self):
        csv_text = "SKU,Name,Unit Cost\nP-001,Widget,10.00\nP-002,Gadget,20.00"
        result = parse_csv(csv_text)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sku"], "P-001")
        self.assertEqual(result[0]["name"], "Widget")
        self.assertEqual(result[0]["unit cost"], "10.00")
        self.assertEqual(result[1]["sku"], "P-002")

    def test_parse_csv_strips_whitespace(self):
        csv_text = " SKU , Name , Unit Cost \n  P-001 , Widget , 10.00 "
        result = parse_csv(csv_text)

        self.assertEqual(len(result), 1)
        self.assertIn("sku", result[0])
        self.assertIn("name", result[0])
        self.assertEqual(result[0]["sku"], "P-001")
        self.assertEqual(result[0]["name"], "Widget")
        self.assertEqual(result[0]["unit cost"], "10.00")

    def test_parse_csv_empty(self):
        result = parse_csv("")
        self.assertEqual(result, [])

    def test_parse_csv_file_object(self):
        csv_text = "sku,name\nA-001,Alpha"
        buf = BytesIO(csv_text.encode("utf-8"))
        result = parse_csv(buf)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["sku"], "A-001")

    def test_parse_csv_keys_lowercased(self):
        csv_text = "SKU,NAME,Description\nX-1,Xylophone,Musical instrument"
        result = parse_csv(csv_text)

        self.assertEqual(len(result), 1)
        self.assertIn("sku", result[0])
        self.assertIn("name", result[0])
        self.assertIn("description", result[0])


class ParseExcelTests(TestCase):
    """Tests for ``parse_excel``."""

    @staticmethod
    def _make_workbook(headers, rows):
        """Create an in-memory Excel file and return a BytesIO."""
        wb = Workbook()
        ws = wb.active
        ws.append(headers)
        for row in rows:
            ws.append(row)
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        return buf

    def test_parse_excel_basic(self):
        buf = self._make_workbook(
            ["sku", "name", "unit_cost"],
            [
                ["P-001", "Widget", "10.00"],
                ["P-002", "Gadget", "20.00"],
            ],
        )
        result = parse_excel(buf)

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["sku"], "P-001")
        self.assertEqual(result[0]["name"], "Widget")
        self.assertEqual(result[0]["unit_cost"], "10.00")
        self.assertEqual(result[1]["sku"], "P-002")

    def test_parse_excel_empty(self):
        wb = Workbook()
        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)
        result = parse_excel(buf)

        self.assertEqual(result, [])

    def test_parse_excel_keys_lowercased(self):
        buf = self._make_workbook(
            ["SKU", "Name", "Unit Cost"],
            [["X-1", "Xylophone", "5.00"]],
        )
        result = parse_excel(buf)

        self.assertEqual(len(result), 1)
        self.assertIn("sku", result[0])
        self.assertIn("name", result[0])
        self.assertIn("unit cost", result[0])

    def test_parse_excel_skips_blank_rows(self):
        buf = self._make_workbook(
            ["sku", "name"],
            [
                ["P-001", "Widget"],
                [None, None],
                ["P-002", "Gadget"],
            ],
        )
        result = parse_excel(buf)

        self.assertEqual(len(result), 2)

    def test_parse_excel_none_values_become_empty_string(self):
        buf = self._make_workbook(
            ["sku", "name", "description"],
            [["P-001", "Widget", None]],
        )
        result = parse_excel(buf)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["description"], "")
