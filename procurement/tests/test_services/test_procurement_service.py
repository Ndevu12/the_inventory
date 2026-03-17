"""Integration tests for ProcurementService workflows.

Tests exercise the full flow: confirm orders, cancel orders, and
receive goods (which auto-creates stock movements via StockService).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import StockMovement, StockRecord
from inventory.tests.factories import create_location, create_product

from procurement.models import PurchaseOrderStatus
from procurement.services.procurement import ProcurementService

from ..factories import (
    create_goods_received_note,
    create_purchase_order,
    create_purchase_order_line,
    create_supplier,
)


class ProcurementServiceSetupMixin:
    """Shared setUp for ProcurementService tests."""

    def setUp(self):
        self.service = ProcurementService()
        self.supplier = create_supplier()
        self.product_a = create_product(sku="PROC-A", unit_cost=Decimal("10.00"))
        self.product_b = create_product(sku="PROC-B", unit_cost=Decimal("25.00"))
        self.warehouse = create_location(name="Main Warehouse")


# =====================================================================
# Confirm Order
# =====================================================================


class ProcurementServiceConfirmTests(ProcurementServiceSetupMixin, TestCase):
    """Test purchase order confirmation."""

    def test_confirm_draft_order(self):
        po = create_purchase_order(supplier=self.supplier)
        create_purchase_order_line(
            purchase_order=po, product=self.product_a,
        )
        result = self.service.confirm_order(purchase_order=po)
        self.assertEqual(result.status, PurchaseOrderStatus.CONFIRMED)

    def test_confirm_order_without_lines_raises_error(self):
        po = create_purchase_order(
            order_number="PO-EMPTY",
            supplier=self.supplier,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.confirm_order(purchase_order=po)
        self.assertIn("no line items", str(ctx.exception.message))

    def test_confirm_already_confirmed_raises_error(self):
        po = create_purchase_order(
            order_number="PO-CONF",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.confirm_order(purchase_order=po)
        self.assertIn("Only draft", str(ctx.exception.message))

    def test_confirm_cancelled_raises_error(self):
        po = create_purchase_order(
            order_number="PO-CANC",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CANCELLED,
        )
        with self.assertRaises(ValidationError):
            self.service.confirm_order(purchase_order=po)


# =====================================================================
# Cancel Order
# =====================================================================


class ProcurementServiceCancelTests(ProcurementServiceSetupMixin, TestCase):
    """Test purchase order cancellation."""

    def test_cancel_draft_order(self):
        po = create_purchase_order(
            order_number="PO-CDRAFT",
            supplier=self.supplier,
        )
        result = self.service.cancel_order(purchase_order=po)
        self.assertEqual(result.status, PurchaseOrderStatus.CANCELLED)

    def test_cancel_confirmed_order(self):
        po = create_purchase_order(
            order_number="PO-CCONF",
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        result = self.service.cancel_order(purchase_order=po)
        self.assertEqual(result.status, PurchaseOrderStatus.CANCELLED)

    def test_cancel_received_order_raises_error(self):
        po = create_purchase_order(
            order_number="PO-CRECV",
            supplier=self.supplier,
            status=PurchaseOrderStatus.RECEIVED,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.cancel_order(purchase_order=po)
        self.assertIn("Only draft or confirmed", str(ctx.exception.message))


# =====================================================================
# Receive Goods
# =====================================================================


class ProcurementServiceReceiveTests(ProcurementServiceSetupMixin, TestCase):
    """Test goods receiving flow with stock movement creation."""

    def _make_confirmed_po_with_lines(self, order_number="PO-RCV-001"):
        """Helper to create a confirmed PO with two line items."""
        po = create_purchase_order(
            order_number=order_number,
            supplier=self.supplier,
            status=PurchaseOrderStatus.CONFIRMED,
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_a,
            quantity=100,
            unit_cost=Decimal("10.00"),
        )
        create_purchase_order_line(
            purchase_order=po,
            product=self.product_b,
            quantity=50,
            unit_cost=Decimal("25.00"),
        )
        return po

    def test_receive_creates_stock_movements(self):
        po = self._make_confirmed_po_with_lines()
        grn = create_goods_received_note(
            purchase_order=po, location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)

        movements = StockMovement.objects.filter(reference=grn.grn_number)
        self.assertEqual(movements.count(), 2)

    def test_receive_updates_stock_records(self):
        po = self._make_confirmed_po_with_lines()
        grn = create_goods_received_note(
            purchase_order=po, location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)

        record_a = StockRecord.objects.get(
            product=self.product_a, location=self.warehouse,
        )
        record_b = StockRecord.objects.get(
            product=self.product_b, location=self.warehouse,
        )
        self.assertEqual(record_a.quantity, 100)
        self.assertEqual(record_b.quantity, 50)

    def test_receive_marks_grn_as_processed(self):
        po = self._make_confirmed_po_with_lines()
        grn = create_goods_received_note(
            purchase_order=po, location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)
        grn.refresh_from_db()
        self.assertTrue(grn.is_processed)

    def test_receive_transitions_po_to_received(self):
        po = self._make_confirmed_po_with_lines()
        grn = create_goods_received_note(
            purchase_order=po, location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)
        po.refresh_from_db()
        self.assertEqual(po.status, PurchaseOrderStatus.RECEIVED)

    def test_receive_already_processed_raises_error(self):
        po = self._make_confirmed_po_with_lines(order_number="PO-RCV-DUP")
        grn = create_goods_received_note(
            grn_number="GRN-DUP",
            purchase_order=po,
            location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)

        with self.assertRaises(ValidationError) as ctx:
            self.service.receive_goods(goods_received_note=grn)
        self.assertIn("already been processed", str(ctx.exception.message))

    def test_receive_draft_po_raises_error(self):
        po = create_purchase_order(
            order_number="PO-RCV-DRAFT",
            supplier=self.supplier,
            status=PurchaseOrderStatus.DRAFT,
        )
        grn = create_goods_received_note(
            grn_number="GRN-DRAFT",
            purchase_order=po,
            location=self.warehouse,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.receive_goods(goods_received_note=grn)
        self.assertIn("must be confirmed", str(ctx.exception.message))

    def test_receive_sets_movement_reference_to_grn_number(self):
        po = self._make_confirmed_po_with_lines(order_number="PO-RCV-REF")
        grn = create_goods_received_note(
            grn_number="GRN-REF-001",
            purchase_order=po,
            location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)

        for movement in StockMovement.objects.filter(reference="GRN-REF-001"):
            self.assertEqual(movement.reference, "GRN-REF-001")
            self.assertEqual(movement.to_location, self.warehouse)

    def test_receive_preserves_unit_cost_on_movements(self):
        po = self._make_confirmed_po_with_lines(order_number="PO-RCV-COST")
        grn = create_goods_received_note(
            grn_number="GRN-COST",
            purchase_order=po,
            location=self.warehouse,
        )
        self.service.receive_goods(goods_received_note=grn)

        movement_a = StockMovement.objects.get(
            reference="GRN-COST", product=self.product_a,
        )
        movement_b = StockMovement.objects.get(
            reference="GRN-COST", product=self.product_b,
        )
        self.assertEqual(movement_a.unit_cost, Decimal("10.00"))
        self.assertEqual(movement_b.unit_cost, Decimal("25.00"))
