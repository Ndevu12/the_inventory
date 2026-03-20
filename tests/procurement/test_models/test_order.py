"""Unit tests for PurchaseOrder, PurchaseOrderLine, and GoodsReceivedNote models."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from tests.fixtures.factories import create_location, create_product
from tests.fixtures.factories import create_tenant

from procurement.models import PurchaseOrderLine, PurchaseOrderStatus

from ..factories import (
    create_goods_received_note,
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)


# =====================================================================
# PurchaseOrder
# =====================================================================


class PurchaseOrderCreationTests(TestCase):
    """Test PurchaseOrder creation and field defaults."""

    def setUp(self):
        self.tenant = create_tenant()
        self.supplier = create_supplier(tenant=self.tenant)

    def test_create_draft_order(self):
        po = create_purchase_order(supplier=self.supplier, tenant=self.tenant)
        self.assertEqual(po.status, PurchaseOrderStatus.DRAFT)
        self.assertEqual(po.supplier, self.supplier)

    def test_str_representation(self):
        po = create_purchase_order(
            order_number="PO-STR-001",
            supplier=self.supplier,
            tenant=self.tenant,
        )
        self.assertEqual(str(po), f"PO-STR-001 — {self.supplier.name}")

    def test_order_number_must_be_unique(self):
        create_purchase_order(
            order_number="PO-UNIQ",
            supplier=self.supplier,
            tenant=self.tenant,
        )
        with self.assertRaises(IntegrityError):
            create_purchase_order(
                order_number="PO-UNIQ",
                supplier=create_supplier(code="SUP-002", tenant=self.tenant),
                tenant=self.tenant,
            )

    def test_expected_delivery_before_order_date_raises_error(self):
        po = create_purchase_order(
            order_number="PO-DATE",
            supplier=self.supplier,
            tenant=self.tenant,
            order_date=date.today(),
            expected_delivery_date=date.today() - timedelta(days=5),
        )
        with self.assertRaises(ValidationError) as ctx:
            po.full_clean()
        self.assertIn("expected_delivery_date", ctx.exception.message_dict)


# =====================================================================
# PurchaseOrderLine
# =====================================================================


class PurchaseOrderLineTests(TestCase):
    """Test PurchaseOrderLine creation and computed properties."""

    def setUp(self):
        self.tenant = create_tenant()
        self.supplier = create_supplier(tenant=self.tenant)
        self.po = create_purchase_order(supplier=self.supplier, tenant=self.tenant)
        self.product = create_product(sku="LINE-001", tenant=self.tenant)

    def test_create_line(self):
        line = create_purchase_order_line(
            purchase_order=self.po,
            product=self.product,
            quantity=50,
            unit_cost=Decimal("5.00"),
        )
        self.assertEqual(line.quantity, 50)
        self.assertEqual(line.unit_cost, Decimal("5.00"))

    def test_line_total(self):
        line = create_purchase_order_line(
            purchase_order=self.po,
            product=self.product,
            quantity=20,
            unit_cost=Decimal("3.50"),
        )
        self.assertEqual(line.line_total, Decimal("70.00"))

    def test_str_representation(self):
        line = create_purchase_order_line(
            purchase_order=self.po,
            product=self.product,
            quantity=10,
            unit_cost=Decimal("2.00"),
        )
        self.assertEqual(str(line), "LINE-001 x10 @ 2.00")

    def test_unique_product_per_order(self):
        create_purchase_order_line(
            purchase_order=self.po,
            product=self.product,
        )
        with self.assertRaises(IntegrityError):
            create_purchase_order_line(
                purchase_order=self.po,
                product=self.product,
            )

    def test_total_cost_across_lines(self):
        p1 = create_product(sku="TOTAL-001", tenant=self.tenant)
        p2 = create_product(sku="TOTAL-002", tenant=self.tenant)
        create_purchase_order_line(
            purchase_order=self.po,
            product=p1,
            quantity=10,
            unit_cost=Decimal("5.00"),
        )
        create_purchase_order_line(
            purchase_order=self.po,
            product=p2,
            quantity=5,
            unit_cost=Decimal("20.00"),
        )
        self.assertEqual(self.po.total_cost, Decimal("150.00"))

    def test_line_tenant_populated_and_matches_purchase_order(self):
        tenant = create_tenant()
        supplier = create_supplier(tenant=tenant)
        po = create_purchase_order(supplier=supplier, tenant=tenant)
        product = create_product(sku="TEN-LINE", tenant=tenant)
        line = create_purchase_order_line(purchase_order=po, product=product)
        line.refresh_from_db()
        self.assertEqual(line.tenant, tenant)
        self.assertEqual(line.tenant, po.tenant)

    def test_save_sets_tenant_from_purchase_order_when_omitted(self):
        tenant = create_tenant()
        supplier = create_supplier(tenant=tenant)
        po = create_purchase_order(supplier=supplier, tenant=tenant)
        product = create_product(sku="AUTO-TEN", tenant=tenant)
        line = PurchaseOrderLine(
            purchase_order=po,
            product=product,
            quantity=1,
            unit_cost=Decimal("1.00"),
        )
        line.save()
        line.refresh_from_db()
        self.assertEqual(line.tenant, tenant)

    def test_tenant_mismatch_raises_validation_error(self):
        t1 = create_tenant()
        t2 = create_tenant()
        po = create_purchase_order(
            tenant=t1,
            supplier=create_supplier(tenant=t1),
        )
        product = create_product(sku="MIS-TEN", tenant=t1)
        line = PurchaseOrderLine(
            purchase_order=po,
            product=product,
            quantity=1,
            unit_cost=Decimal("1.00"),
            tenant=t2,
        )
        with self.assertRaises(ValidationError):
            line.save()

    def test_filter_lines_by_tenant(self):
        t1 = create_tenant()
        t2 = create_tenant()
        po1 = create_purchase_order(
            tenant=t1,
            supplier=create_supplier(tenant=t1),
        )
        po2 = create_purchase_order(
            tenant=t2,
            supplier=create_supplier(code="SUP-T2", tenant=t2),
        )
        p1 = create_product(sku="FIL-1", tenant=t1)
        p2 = create_product(sku="FIL-2", tenant=t2)
        line1 = create_purchase_order_line(purchase_order=po1, product=p1)
        line2 = create_purchase_order_line(purchase_order=po2, product=p2)
        self.assertEqual(
            list(PurchaseOrderLine.objects.filter(tenant=t1).order_by("id")),
            [line1],
        )
        self.assertEqual(
            list(PurchaseOrderLine.objects.filter(tenant=t2).order_by("id")),
            [line2],
        )


# =====================================================================
# GoodsReceivedNote
# =====================================================================


class GoodsReceivedNoteTests(TestCase):
    """Test GoodsReceivedNote creation and field defaults."""

    def test_create_grn(self):
        tenant = create_tenant()
        supplier = create_supplier(code="SUP-GRN", tenant=tenant)
        po = create_purchase_order(
            order_number="PO-GRN-001",
            supplier=supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Dock A", tenant=tenant)
        grn = create_goods_received_note(
            grn_number="GRN-001",
            purchase_order=po,
            location=location,
            tenant=tenant,
        )
        self.assertFalse(grn.is_processed)
        self.assertEqual(grn.purchase_order, po)

    def test_str_representation(self):
        tenant = create_tenant()
        supplier = create_supplier(code="SUP-GRNSTR", tenant=tenant)
        po = create_purchase_order(
            order_number="PO-GRNSTR",
            supplier=supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Dock B", tenant=tenant)
        grn = create_goods_received_note(
            grn_number="GRN-STR",
            purchase_order=po,
            location=location,
            tenant=tenant,
        )
        self.assertEqual(str(grn), "GRN-STR — PO-GRNSTR")

    def test_grn_number_must_be_unique(self):
        tenant = create_tenant()
        supplier = create_supplier(code="SUP-GRNUNIQ", tenant=tenant)
        po = create_purchase_order(
            order_number="PO-GRNUNIQ",
            supplier=supplier,
            status=PurchaseOrderStatus.CONFIRMED,
            tenant=tenant,
        )
        location = create_location(name="Dock C", tenant=tenant)
        create_goods_received_note(
            grn_number="GRN-UNIQ",
            purchase_order=po,
            location=location,
            tenant=tenant,
        )
        with self.assertRaises(IntegrityError):
            create_goods_received_note(
                grn_number="GRN-UNIQ",
                purchase_order=po,
                location=location,
                tenant=tenant,
            )
