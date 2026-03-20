"""Tests for OrderReportService."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from tests.fixtures.factories import create_product, create_tenant
from tenants.context import set_current_tenant, clear_current_tenant

from procurement.models import PurchaseOrderStatus
from tests.procurement.factories import (
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)

from reports.services.order_reports import OrderReportService

from sales.models import SalesOrderStatus
from tests.sales.factories import (
    create_customer,
    create_sales_order,
    create_sales_order_line,
)


class OrderReportServiceSetupMixin:
    """Shared setUp with sample orders."""

    def setUp(self):
        self.service = OrderReportService()
        self.tenant = create_tenant()
        set_current_tenant(self.tenant)
        self.product_a = create_product(
            sku="ORD-A", unit_cost=Decimal("10.00"), tenant=self.tenant
        )
        self.product_b = create_product(
            sku="ORD-B", unit_cost=Decimal("25.00"), tenant=self.tenant
        )


# =====================================================================
# Purchase Reports
# =====================================================================


class PurchaseSummaryTests(OrderReportServiceSetupMixin, TestCase):
    """Test purchase order summary aggregations."""

    def setUp(self):
        super().setUp()
        self.supplier = create_supplier(tenant=self.tenant)

    def test_monthly_summary_with_orders(self):
        po = create_purchase_order(
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=self.tenant,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_cost"], Decimal("100.00"))

    def test_excludes_cancelled_orders(self):
        po = create_purchase_order(
            order_number="PO-RPT-CANC",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CANCELLED,
            tenant=self.tenant,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 0)

    def test_purchase_totals(self):
        po1 = create_purchase_order(
            order_number="PO-RPT-T1",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=self.tenant,
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
            tenant=self.tenant,
        )
        create_purchase_order_line(
            purchase_order=po2,
            product=self.product_b,
            quantity=5,
            unit_cost=Decimal("25.00"),
        )
        totals = self.service.get_purchase_totals(tenant=self.tenant)
        self.assertEqual(totals["order_count"], 2)
        self.assertEqual(totals["line_count"], 2)
        self.assertEqual(totals["total_cost"], Decimal("225.00"))

    def test_date_filter(self):
        po = create_purchase_order(
            order_number="PO-RPT-DATE",
            supplier=self.supplier,
            order_date=date.today() - timedelta(days=60),
            tenant=self.tenant,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=10,
            unit_cost=Decimal("10.00"),
        )
        summary = self.service.get_purchase_summary(
            tenant=self.tenant,
            period="monthly",
            date_from=date.today() - timedelta(days=30),
        )
        self.assertEqual(len(summary), 0)

    def test_unknown_period_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.get_purchase_summary(tenant=self.tenant, period="yearly")

    def test_no_tenant_raises_error(self):
        """Test that ValueError is raised when no tenant is provided."""
        clear_current_tenant()
        with self.assertRaises(ValueError) as ctx:
            self.service.get_purchase_summary(tenant=None, period="monthly")
        self.assertIn("No tenant", str(ctx.exception))

    def test_cross_tenant_isolation(self):
        """Test that purchase orders from other tenants are not included."""
        other_tenant = create_tenant()
        other_supplier = create_supplier(tenant=other_tenant)
        other_po = create_purchase_order(
            order_number="PO-OTHER-TENANT",
            supplier=other_supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=other_tenant,
        )
        set_current_tenant(other_tenant)
        create_purchase_order_line(
            purchase_order=other_po,
            product=create_product(sku="OTHER-SKU", tenant=other_tenant),
            quantity=10,
            unit_cost=Decimal("10.00"),
        )

        # Create order in current tenant
        set_current_tenant(self.tenant)
        po = create_purchase_order(
            order_number="PO-CURRENT-TENANT",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=self.tenant,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=5,
            unit_cost=Decimal("10.00"),
        )

        # Query with current tenant should only return current tenant's data
        summary = self.service.get_purchase_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_cost"], Decimal("50.00"))


# =====================================================================
# Sales Reports
# =====================================================================


class SalesSummaryTests(OrderReportServiceSetupMixin, TestCase):
    """Test sales order summary aggregations."""

    def setUp(self):
        super().setUp()
        self.customer = create_customer(tenant=self.tenant)

    def test_monthly_summary_with_orders(self):
        so = create_sales_order(
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=self.tenant,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_revenue"], Decimal("150.00"))

    def test_excludes_cancelled_orders(self):
        so = create_sales_order(
            order_number="SO-RPT-CANC",
            customer=self.customer,
            status=SalesOrderStatus.CANCELLED,
            tenant=self.tenant,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 0)

    def test_sales_totals(self):
        so1 = create_sales_order(
            order_number="SO-RPT-T1",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=self.tenant,
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
            tenant=self.tenant,
        )
        create_sales_order_line(
            sales_order=so2,
            product=self.product_b,
            quantity=5,
            unit_price=Decimal("40.00"),
        )
        totals = self.service.get_sales_totals(tenant=self.tenant)
        self.assertEqual(totals["order_count"], 2)
        self.assertEqual(totals["line_count"], 2)
        self.assertEqual(totals["total_revenue"], Decimal("350.00"))

    def test_date_filter(self):
        so = create_sales_order(
            order_number="SO-RPT-DATE",
            customer=self.customer,
            order_date=date.today() - timedelta(days=60),
            tenant=self.tenant,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=10,
            unit_price=Decimal("15.00"),
        )
        summary = self.service.get_sales_summary(
            tenant=self.tenant,
            period="monthly",
            date_from=date.today() - timedelta(days=30),
        )
        self.assertEqual(len(summary), 0)

    def test_no_tenant_raises_error(self):
        """Test that ValueError is raised when no tenant is provided."""
        clear_current_tenant()
        with self.assertRaises(ValueError) as ctx:
            self.service.get_sales_summary(tenant=None, period="monthly")
        self.assertIn("No tenant", str(ctx.exception))

    def test_cross_tenant_isolation(self):
        """Test that sales orders from other tenants are not included."""
        other_tenant = create_tenant()
        other_customer = create_customer(tenant=other_tenant)
        other_so = create_sales_order(
            order_number="SO-OTHER-TENANT",
            customer=other_customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=other_tenant,
        )
        set_current_tenant(other_tenant)
        create_sales_order_line(
            sales_order=other_so,
            product=create_product(sku="OTHER-SKU", tenant=other_tenant),
            quantity=10,
            unit_price=Decimal("15.00"),
        )

        # Create order in current tenant
        set_current_tenant(self.tenant)
        so = create_sales_order(
            order_number="SO-CURRENT-TENANT",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
            tenant=self.tenant,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=5,
            unit_price=Decimal("15.00"),
        )

        # Query with current tenant should only return current tenant's data
        summary = self.service.get_sales_summary(
            tenant=self.tenant, period="monthly"
        )
        self.assertEqual(len(summary), 1)
        self.assertEqual(summary[0]["order_count"], 1)
        self.assertEqual(summary[0]["total_revenue"], Decimal("75.00"))
