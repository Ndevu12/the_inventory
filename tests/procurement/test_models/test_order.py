"""Unit tests for PurchaseOrder, PurchaseOrderLine, and GoodsReceivedNote models."""

from datetime import date, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from tests.fixtures.factories import create_location, create_product
from tests.fixtures.factories import create_tenant

from procurement.models import PurchaseOrderStatus

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
        po = create_purchase_order(supplier=self.supplier)
        self.assertEqual(po.status, PurchaseOrderStatus.DRAFT)
        self.assertEqual(po.supplier, self.supplier)

    def test_str_representation(self):
        po = create_purchase_order(
            order_number="PO-STR-001",
            supplier=self.supplier,
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
        self.supplier = create_supplier()
        self.po = create_purchase_order(supplier=self.supplier)
        self.product = create_product(sku="LINE-001")

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
        p1 = create_product(sku="TOTAL-001")
        p2 = create_product(sku="TOTAL-002")
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


# =====================================================================
# GoodsReceivedNote
# =====================================================================


class GoodsReceivedNoteTests(TestCase):
    """Test GoodsReceivedNote creation and field defaults."""

    def test_create_grn(self):
        supplier = create_supplier(code="SUP-GRN")
        po = create_purchase_order(
            order_number="PO-GRN-001",
            supplier=supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        location = create_location(name="Dock A")
        grn = create_goods_received_note(
            grn_number="GRN-001",
            purchase_order=po,
            location=location,
        )
        self.assertFalse(grn.is_processed)
        self.assertEqual(grn.purchase_order, po)

    def test_str_representation(self):
        supplier = create_supplier(code="SUP-GRNSTR")
        po = create_purchase_order(
            order_number="PO-GRNSTR",
            supplier=supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        location = create_location(name="Dock B")
        grn = create_goods_received_note(
            grn_number="GRN-STR",
            purchase_order=po,
            location=location,
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
