"""Integration tests for SalesService workflows.

Tests exercise the full flow: confirm orders, cancel orders, and
process dispatches (which auto-create issue stock movements via StockService).
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import StockMovement, StockRecord
from inventory.services.stock import StockService
from tests.fixtures.factories import create_location, create_product

from sales.models import SalesOrderStatus
from sales.services.sales import SalesService

from ..factories import (
    create_customer,
    create_dispatch,
    create_sales_order,
    create_sales_order_line,
)


class SalesServiceSetupMixin:
    """Shared setUp for SalesService tests."""

    def setUp(self):
        self.service = SalesService()
        self.stock_service = StockService()
        self.customer = create_customer()
        self.product_a = create_product(sku="SALE-A", unit_cost=Decimal("10.00"))
        self.product_b = create_product(sku="SALE-B", unit_cost=Decimal("25.00"))
        self.warehouse = create_location(name="Main Warehouse")


# =====================================================================
# Confirm Order
# =====================================================================


class SalesServiceConfirmTests(SalesServiceSetupMixin, TestCase):
    """Test sales order confirmation."""

    def test_confirm_draft_order(self):
        so = create_sales_order(customer=self.customer)
        create_sales_order_line(
            sales_order=so, product=self.product_a,
        )
        result = self.service.confirm_order(sales_order=so)
        self.assertEqual(result.status, SalesOrderStatus.CONFIRMED)

    def test_confirm_order_without_lines_raises_error(self):
        so = create_sales_order(
            order_number="SO-EMPTY",
            customer=self.customer,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.confirm_order(sales_order=so)
        self.assertIn("no line items", str(ctx.exception.message))

    def test_confirm_already_confirmed_raises_error(self):
        so = create_sales_order(
            order_number="SO-CONF",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.confirm_order(sales_order=so)
        self.assertIn("Only draft", str(ctx.exception.message))

    def test_confirm_cancelled_raises_error(self):
        so = create_sales_order(
            order_number="SO-CANC",
            customer=self.customer,
            status=SalesOrderStatus.CANCELLED,
        )
        with self.assertRaises(ValidationError):
            self.service.confirm_order(sales_order=so)


# =====================================================================
# Cancel Order
# =====================================================================


class SalesServiceCancelTests(SalesServiceSetupMixin, TestCase):
    """Test sales order cancellation."""

    def test_cancel_draft_order(self):
        so = create_sales_order(
            order_number="SO-CDRAFT",
            customer=self.customer,
        )
        result = self.service.cancel_order(sales_order=so)
        self.assertEqual(result.status, SalesOrderStatus.CANCELLED)

    def test_cancel_confirmed_order(self):
        so = create_sales_order(
            order_number="SO-CCONF",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        result = self.service.cancel_order(sales_order=so)
        self.assertEqual(result.status, SalesOrderStatus.CANCELLED)

    def test_cancel_fulfilled_order_raises_error(self):
        so = create_sales_order(
            order_number="SO-CFULFILL",
            customer=self.customer,
            status=SalesOrderStatus.FULFILLED,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.cancel_order(sales_order=so)
        self.assertIn("Only draft or confirmed", str(ctx.exception.message))


# =====================================================================
# Process Dispatch
# =====================================================================


class SalesServiceDispatchTests(SalesServiceSetupMixin, TestCase):
    """Test dispatch flow with stock movement (issue) creation."""

    def _make_confirmed_so_with_stock(self, order_number="SO-DSP-001"):
        """Helper to create a confirmed SO with stock at warehouse."""
        from inventory.models.stock import MovementType

        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=200,
            to_location=self.warehouse,
        )
        self.stock_service.process_movement(
            product=self.product_b,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )

        so = create_sales_order(
            order_number=order_number,
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=50,
            unit_price=Decimal("15.00"),
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_b,
            quantity=20,
            unit_price=Decimal("40.00"),
        )
        return so

    def test_dispatch_creates_stock_movements(self):
        so = self._make_confirmed_so_with_stock()
        dispatch = create_dispatch(
            sales_order=so, from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)

        movements = StockMovement.objects.filter(
            reference=dispatch.dispatch_number,
        )
        self.assertEqual(movements.count(), 2)

    def test_dispatch_decrements_stock_records(self):
        so = self._make_confirmed_so_with_stock()
        dispatch = create_dispatch(
            sales_order=so, from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)

        record_a = StockRecord.objects.get(
            product=self.product_a, location=self.warehouse,
        )
        record_b = StockRecord.objects.get(
            product=self.product_b, location=self.warehouse,
        )
        self.assertEqual(record_a.quantity, 150)  # 200 - 50
        self.assertEqual(record_b.quantity, 80)   # 100 - 20

    def test_dispatch_marks_as_processed(self):
        so = self._make_confirmed_so_with_stock()
        dispatch = create_dispatch(
            sales_order=so, from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)
        dispatch.refresh_from_db()
        self.assertTrue(dispatch.is_processed)

    def test_dispatch_transitions_so_to_fulfilled(self):
        so = self._make_confirmed_so_with_stock()
        dispatch = create_dispatch(
            sales_order=so, from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)
        so.refresh_from_db()
        self.assertEqual(so.status, SalesOrderStatus.FULFILLED)

    def test_dispatch_already_processed_raises_error(self):
        so = self._make_confirmed_so_with_stock(order_number="SO-DSP-DUP")
        dispatch = create_dispatch(
            dispatch_number="DSP-DUP",
            sales_order=so,
            from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)

        with self.assertRaises(ValidationError) as ctx:
            self.service.process_dispatch(dispatch=dispatch)
        self.assertIn("already been processed", str(ctx.exception.message))

    def test_dispatch_draft_so_raises_error(self):
        so = create_sales_order(
            order_number="SO-DSP-DRAFT",
            customer=self.customer,
            status=SalesOrderStatus.DRAFT,
        )
        dispatch = create_dispatch(
            dispatch_number="DSP-DRAFT",
            sales_order=so,
            from_location=self.warehouse,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.process_dispatch(dispatch=dispatch)
        self.assertIn("must be confirmed", str(ctx.exception.message))

    def test_dispatch_insufficient_stock_rolls_back(self):
        """If stock is insufficient, the entire dispatch is rolled back."""
        so = create_sales_order(
            order_number="SO-DSP-INSUF",
            customer=self.customer,
            status=SalesOrderStatus.CONFIRMED,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product_a,
            quantity=9999,
            unit_price=Decimal("15.00"),
        )
        dispatch = create_dispatch(
            dispatch_number="DSP-INSUF",
            sales_order=so,
            from_location=self.warehouse,
        )
        with self.assertRaises(ValidationError):
            self.service.process_dispatch(dispatch=dispatch)

        dispatch.refresh_from_db()
        self.assertFalse(dispatch.is_processed)
        so.refresh_from_db()
        self.assertEqual(so.status, SalesOrderStatus.CONFIRMED)

    def test_dispatch_sets_reference_to_dispatch_number(self):
        so = self._make_confirmed_so_with_stock(order_number="SO-DSP-REF")
        dispatch = create_dispatch(
            dispatch_number="DSP-REF-001",
            sales_order=so,
            from_location=self.warehouse,
        )
        self.service.process_dispatch(dispatch=dispatch)

        for movement in StockMovement.objects.filter(reference="DSP-REF-001"):
            self.assertEqual(movement.reference, "DSP-REF-001")
            self.assertEqual(movement.from_location, self.warehouse)
