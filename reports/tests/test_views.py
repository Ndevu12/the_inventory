"""Tests for report views."""

from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from inventory.models import MovementType
from inventory.services.stock import StockService
from inventory.tests.factories import create_location, create_product, create_stock_record

from procurement.tests.factories import (
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)

from sales.tests.factories import (
    create_customer,
    create_sales_order,
    create_sales_order_line,
)


class ReportViewSetupMixin(WagtailTestUtils):
    """Shared setUp: logged-in admin user with sample data."""

    def setUp(self):
        self.user = self.login()
        self.warehouse = create_location(name="Warehouse")
        self.product = create_product(
            sku="VIEW-A", unit_cost=Decimal("10.00"), reorder_point=20,
        )


# =====================================================================
# Stock Valuation View
# =====================================================================


class StockValuationViewTests(ReportViewSetupMixin, TestCase):

    def test_accessible(self):
        response = self.client.get(reverse("report_stock_valuation"))
        self.assertEqual(response.status_code, 200)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("report_stock_valuation"))
        self.assertEqual(response.status_code, 302)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("report_stock_valuation"))
        self.assertTemplateUsed(response, "reports/stock_valuation.html")

    def test_shows_valuation_data(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        response = self.client.get(reverse("report_stock_valuation"))
        self.assertContains(response, "VIEW-A")

    def test_csv_export(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        response = self.client.get(
            reverse("report_stock_valuation"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_method_parameter(self):
        response = self.client.get(
            reverse("report_stock_valuation"),
            {"method": "latest_cost"},
        )
        self.assertEqual(response.context["current_method"], "latest_cost")


# =====================================================================
# Movement History View
# =====================================================================


class MovementHistoryViewTests(ReportViewSetupMixin, TestCase):

    def setUp(self):
        super().setUp()
        service = StockService()
        service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )

    def test_accessible(self):
        response = self.client.get(reverse("report_movement_history"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("report_movement_history"))
        self.assertTemplateUsed(response, "reports/movement_history.html")

    def test_shows_movements(self):
        response = self.client.get(reverse("report_movement_history"))
        self.assertContains(response, "VIEW-A")
        self.assertEqual(response.context["total_count"], 1)

    def test_csv_export(self):
        response = self.client.get(
            reverse("report_movement_history"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_filter_by_movement_type(self):
        response = self.client.get(
            reverse("report_movement_history"),
            {"movement_type": "issue"},
        )
        self.assertEqual(response.context["total_count"], 0)


# =====================================================================
# Low Stock & Overstock Views
# =====================================================================


class LowStockReportViewTests(ReportViewSetupMixin, TestCase):

    def test_accessible(self):
        response = self.client.get(reverse("report_low_stock"))
        self.assertEqual(response.status_code, 200)

    def test_shows_low_stock_products(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=5,
        )
        response = self.client.get(reverse("report_low_stock"))
        self.assertContains(response, "VIEW-A")
        self.assertEqual(response.context["total_count"], 1)

    def test_csv_export(self):
        response = self.client.get(
            reverse("report_low_stock"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")


class OverstockReportViewTests(ReportViewSetupMixin, TestCase):

    def test_accessible(self):
        response = self.client.get(reverse("report_overstock"))
        self.assertEqual(response.status_code, 200)

    def test_shows_overstocked_products(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        response = self.client.get(reverse("report_overstock"))
        self.assertContains(response, "VIEW-A")

    def test_custom_threshold(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        response = self.client.get(
            reverse("report_overstock"), {"threshold": "10"},
        )
        self.assertEqual(response.context["threshold_multiplier"], 10)

    def test_csv_export(self):
        response = self.client.get(
            reverse("report_overstock"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")


# =====================================================================
# Purchase & Sales Summary Views
# =====================================================================


class PurchaseSummaryViewTests(ReportViewSetupMixin, TestCase):

    def test_accessible(self):
        response = self.client.get(reverse("report_purchase_summary"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("report_purchase_summary"))
        self.assertTemplateUsed(response, "reports/purchase_summary.html")

    def test_shows_summary_data(self):
        supplier = create_supplier()
        po = create_purchase_order(supplier=supplier)
        create_purchase_order_line(
            purchase_order=po,
            product=self.product,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        response = self.client.get(reverse("report_purchase_summary"))
        self.assertEqual(response.context["totals"]["order_count"], 1)

    def test_csv_export(self):
        response = self.client.get(
            reverse("report_purchase_summary"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")


class SalesSummaryViewTests(ReportViewSetupMixin, TestCase):

    def test_accessible(self):
        response = self.client.get(reverse("report_sales_summary"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        response = self.client.get(reverse("report_sales_summary"))
        self.assertTemplateUsed(response, "reports/sales_summary.html")

    def test_shows_summary_data(self):
        customer = create_customer()
        so = create_sales_order(customer=customer)
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        response = self.client.get(reverse("report_sales_summary"))
        self.assertEqual(response.context["totals"]["order_count"], 1)

    def test_csv_export(self):
        response = self.client.get(
            reverse("report_sales_summary"), {"export": "csv"},
        )
        self.assertEqual(response["Content-Type"], "text/csv")
