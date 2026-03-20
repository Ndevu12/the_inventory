"""Tests for OrderReportService."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from tests.fixtures.factories import create_product

from procurement.models import PurchaseOrderStatus
from tests.fixtures.factories import (
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)

from reports.services.order_reports import OrderReportService

from sales.models import SalesOrderStatus
from tests.fixtures.factories import (
    create_customer,
    create_sales_order,
    create_sales_order_line,
)


class OrderReportServiceSetupMixin:
    """Shared setUp with sample orders."""

    def setUp(self):
        self.service = OrderReportService()
        self.product_a = create_product(sku="ORD-A", unit_cost=Decimal("10.00"))
        self.product_b = create_product(sku="ORD-B", unit_cost=Decimal("25.00"))


# =====================================================================
# Purchase Reports
# =====================================================================


class PurchaseSummaryTests(OrderReportServiceSetupMixin, TestCase):
    """Test purchase order summary aggregations."""

    def setUp(self):
        super().setUp()
        self.supplier = create_supplier()

    def test_monthly_summary_with_orders(self):
        po = create_purchase_order(
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(period="monthly")
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_cost"], Decimal("100.00"))

    def test_excludes_cancelled_orders(self):
        po = create_purchase_order(
            order_number="PO-RPT-CANC",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CANCELLED,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(period="monthly")
        self.assertEqual(len(summary), 0)

    def test_purchase_totals(self):
        po1 = create_purchase_order(
            order_number="PO-RPT-T1",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_purchase_order_line(
            purchase_order=po1,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        po2 = create_purchase_order(
            order_number="PO-RPT-T2",
            supplier=self.supplier,
            status=PurchaseOrderStatus.DRAFT,
        )
        create_purchase_order_line(
            purchase_order=po2,
            product=self.product_b,
            quantity=5,
            unit_cost=Decimal("25.00"),
        )
        totals = self.service.get_purchase_totals()
        self.assertEqual(totals["order_count"], 2)
        self.assertEqual(totals["line_count"], 2)
        self.assertEqual(totals["total_cost"], Decimal("225.00"))

    def test_date_filter(self):
        po = create_purchase_order(
            order_number="PO-RPT-DATE",
            supplier=self.supplier,
            order_date=date.today() - timedelta(days=60),
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(
            period="monthly",
            date_from=date.today() - timedelta(days=30),
        )
        self.assertEqual(len(summary), 0)

    def test_unknown_period_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.get_purchase_summary(period="yearly")


# =====================================================================
# Sales Reports
# =====================================================================


class SalesSummaryTests(OrderReportServiceSetupMixin, TestCase):
    """Test sales order summary aggregations."""

    def setUp(self):
        super().setUp()
        self.customer = create_customer()

    def test_monthly_summary_with_orders(self):
        so = create_sales_order(
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(period="monthly")
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_revenue"], Decimal("150.00"))

    def test_excludes_cancelled_orders(self):
        so = create_sales_order(
            order_number="SO-RPT-CANC",
            customer=self.customer,
            status=SalesOrderStatus.CANCELLED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(period="monthly")
        self.assertEqual(len(summary), 0)

    def test_sales_totals(self):
        so1 = create_sales_order(
            order_number="SO-RPT-T1",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so1,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        so2 = create_sales_order(
            order_number="SO-RPT-T2",
            customer=self.customer,
            status=SalesOrderStatus.DRAFT,
        )
        create_sales_order_line(
            sales_order=so2,
            product=self.product_b,
            quantity=5,
            unit_price=Decimal("40.00"),
        )
        totals = self.service.get_sales_totals()
        self.assertEqual(totals["order_count"], 2)
        self.assertEqual(totals["line_count"], 2)
        self.assertEqual(totals["total_revenue"], Decimal("350.00"))

    def test_date_filter(self):
        so = create_sales_order(
            order_number="SO-RPT-DATE",
            customer=self.customer,
            order_date=date.today() - timedelta(days=60),
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(
            period="monthly",
            date_from=date.today() - timedelta(days=30),
        )
        self.assertEqual(len(summary), 0)
