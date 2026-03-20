"""Integration tests verifying that the tenant FK on TimeStampedModel
works correctly across all apps.
"""

from datetime import date
from decimal import Decimal

from django.test import TestCase

from inventory.models import Category, Product, StockLocation, StockRecord
from procurement.models import GoodsReceivedNote, PurchaseOrder, PurchaseOrderLine, Supplier
from sales.models import Customer, Dispatch, SalesOrder, SalesOrderLine
from tests.fixtures.factories import create_tenant, create_user


class InventoryTenantAwareTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()

    def test_product_has_tenant(self):
        p = Product.objects.create(
            sku="P-001", name="Widget", tenant=self.tenant
        )
        p.refresh_from_db()
        self.assertEqual(p.tenant, self.tenant)

    def test_category_has_tenant(self):
        c = Category.add_root(name="Electronics", slug="electronics", tenant=self.tenant)
        c.refresh_from_db()
        self.assertEqual(c.tenant, self.tenant)

    def test_stock_location_has_tenant(self):
        loc = StockLocation.add_root(name="Main WH", tenant=self.tenant)
        loc.refresh_from_db()
        self.assertEqual(loc.tenant, self.tenant)

    def test_stock_record_has_tenant(self):
        p = Product.objects.create(sku="P-002", name="Gizmo", tenant=self.tenant)
        loc = StockLocation.add_root(name="WH-1", tenant=self.tenant)
        sr = StockRecord.objects.create(
            product=p, location=loc, quantity=10, tenant=self.tenant
        )
        sr.refresh_from_db()
        self.assertEqual(sr.tenant, self.tenant)

    def test_cross_tenant_isolation(self):
        t2 = create_tenant()
        Product.objects.create(sku="P-A", name="A", tenant=self.tenant)
        Product.objects.create(sku="P-B", name="B", tenant=t2)
        self.assertEqual(Product.objects.filter(tenant=self.tenant).count(), 1)
        self.assertEqual(Product.objects.filter(tenant=t2).count(), 1)


class ProcurementTenantAwareTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()
        self.user = create_user()

    def test_supplier_has_tenant(self):
        s = Supplier.objects.create(
            code="SUP-001", name="SupplierCo", tenant=self.tenant
        )
        s.refresh_from_db()
        self.assertEqual(s.tenant, self.tenant)

    def test_purchase_order_has_tenant(self):
        s = Supplier.objects.create(
            code="SUP-002", name="Vendor", tenant=self.tenant
        )
        po = PurchaseOrder.objects.create(
            order_number="PO-001",
            supplier=s,
            order_date=date.today(),
            tenant=self.tenant,
        )
        po.refresh_from_db()
        self.assertEqual(po.tenant, self.tenant)

    def test_purchase_order_line_has_tenant(self):
        s = Supplier.objects.create(code="SUP-003", name="V", tenant=self.tenant)
        po = PurchaseOrder.objects.create(
            order_number="PO-002",
            supplier=s,
            order_date=date.today(),
            tenant=self.tenant,
        )
        p = Product.objects.create(sku="P-X", name="Prod", tenant=self.tenant)
        line = PurchaseOrderLine.objects.create(
            purchase_order=po,
            product=p,
            quantity=5,
            unit_cost=Decimal("10.00"),
            tenant=self.tenant,
        )
        line.refresh_from_db()
        self.assertEqual(line.tenant, self.tenant)

    def test_grn_has_tenant(self):
        s = Supplier.objects.create(code="SUP-004", name="V2", tenant=self.tenant)
        po = PurchaseOrder.objects.create(
            order_number="PO-003",
            supplier=s,
            order_date=date.today(),
            tenant=self.tenant,
        )
        loc = StockLocation.add_root(name="Dock", tenant=self.tenant)
        grn = GoodsReceivedNote.objects.create(
            grn_number="GRN-001",
            purchase_order=po,
            received_date=date.today(),
            location=loc,
            tenant=self.tenant,
        )
        grn.refresh_from_db()
        self.assertEqual(grn.tenant, self.tenant)


class SalesTenantAwareTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()

    def test_customer_has_tenant(self):
        c = Customer.objects.create(
            code="C-001", name="Buyer Inc", tenant=self.tenant
        )
        c.refresh_from_db()
        self.assertEqual(c.tenant, self.tenant)

    def test_sales_order_has_tenant(self):
        c = Customer.objects.create(
            code="C-002", name="Client", tenant=self.tenant
        )
        so = SalesOrder.objects.create(
            order_number="SO-001",
            customer=c,
            order_date=date.today(),
            tenant=self.tenant,
        )
        so.refresh_from_db()
        self.assertEqual(so.tenant, self.tenant)

    def test_sales_order_line_has_tenant(self):
        c = Customer.objects.create(code="C-003", name="B", tenant=self.tenant)
        so = SalesOrder.objects.create(
            order_number="SO-002",
            customer=c,
            order_date=date.today(),
            tenant=self.tenant,
        )
        p = Product.objects.create(sku="P-Y", name="Item", tenant=self.tenant)
        line = SalesOrderLine.objects.create(
            sales_order=so,
            product=p,
            quantity=3,
            unit_price=Decimal("25.00"),
            tenant=self.tenant,
        )
        line.refresh_from_db()
        self.assertEqual(line.tenant, self.tenant)

    def test_dispatch_has_tenant(self):
        c = Customer.objects.create(code="C-004", name="D", tenant=self.tenant)
        so = SalesOrder.objects.create(
            order_number="SO-003",
            customer=c,
            order_date=date.today(),
            tenant=self.tenant,
        )
        loc = StockLocation.add_root(name="Dispatch Bay", tenant=self.tenant)
        d = Dispatch.objects.create(
            dispatch_number="DSP-001",
            sales_order=so,
            dispatch_date=date.today(),
            from_location=loc,
            tenant=self.tenant,
        )
        d.refresh_from_db()
        self.assertEqual(d.tenant, self.tenant)
