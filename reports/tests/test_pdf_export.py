"""Tests for PDF export functionality."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from inventory.tests.factories import create_location, create_product, create_stock_record
from reports.pdf import export_pdf


class ExportPdfFunctionTests(TestCase):
    """Direct tests for the ``export_pdf`` helper."""

    def test_export_pdf_returns_pdf_response(self):
        response = export_pdf(
            filename="test_report.pdf",
            title="Test Report",
            headers=["Col A", "Col B", "Col C"],
            rows=[
                ["A1", "B1", "C1"],
                ["A2", "B2", "C2"],
            ],
        )

        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("test_report.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_pdf_empty_rows(self):
        response = export_pdf(
            filename="empty.pdf",
            title="Empty Report",
            headers=["Col A", "Col B"],
            rows=[],
        )

        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("empty.pdf", response["Content-Disposition"])
        self.assertTrue(len(response.content) > 0)

    def test_export_pdf_portrait_mode(self):
        response = export_pdf(
            filename="portrait.pdf",
            title="Portrait Report",
            headers=["Name", "Value"],
            rows=[["Widget", "100"]],
            orientation="portrait",
        )

        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("portrait.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    def test_export_pdf_with_subtitle(self):
        response = export_pdf(
            filename="subtitle.pdf",
            title="Subtitle Report",
            headers=["A"],
            rows=[["1"]],
            subtitle="Filter: last 30 days",
        )

        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_export_pdf_decimal_and_none_values(self):
        response = export_pdf(
            filename="types.pdf",
            title="Mixed Types",
            headers=["Decimal", "None", "String"],
            rows=[
                [Decimal("19.99"), None, "text"],
            ],
        )

        self.assertEqual(response["Content-Type"], "application/pdf")


class StockValuationPdfExportTests(WagtailTestUtils, TestCase):
    """Integration test: stock valuation view with ``?export=pdf``."""

    def setUp(self):
        self.user = self.login()
        self.warehouse = create_location(name="PDF Warehouse")
        self.product = create_product(
            sku="PDF-001",
            name="PDF Widget",
            unit_cost=Decimal("25.00"),
            reorder_point=10,
        )
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )

    def test_stock_valuation_pdf_export(self):
        url = reverse("report_stock_valuation")
        response = self.client.get(url, {"export": "pdf"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))


class LowStockPdfExportTests(WagtailTestUtils, TestCase):
    """Integration test: low stock report view with ``?export=pdf``."""

    def setUp(self):
        self.user = self.login()
        self.warehouse = create_location(name="Low Stock WH")
        self.product = create_product(
            sku="LOW-001",
            name="Low Stock Item",
            unit_cost=Decimal("5.00"),
            reorder_point=20,
        )
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=3,
        )

    def test_low_stock_pdf_export(self):
        url = reverse("report_low_stock")
        response = self.client.get(url, {"export": "pdf"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))
