"""Integration tests for StockService movement processing.

These tests exercise the full flow: create a movement via
:meth:`StockService.process_movement` and verify that StockRecords
are updated correctly, including edge cases like insufficient stock,
transaction atomicity, and multi-step movement sequences.
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from inventory.models import MovementType, StockRecord
from inventory.services.stock import StockService

from ..factories import create_location, create_product, create_stock_record


class StockServiceSetupMixin:
    """Shared setUp for StockService tests."""

    def setUp(self):
        self.service = StockService()
        self.product = create_product(sku="SVC-001", unit_cost=Decimal("10.00"))
        self.warehouse = create_location(name="Warehouse")
        self.store = create_location(name="Store")


# =====================================================================
# Receive
# =====================================================================


class StockServiceReceiveTests(StockServiceSetupMixin, TestCase):
    """Test RECEIVE movement processing."""

    def test_receive_creates_stock_record(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        self.assertEqual(movement.movement_type, MovementType.RECEIVE)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)

    def test_receive_increments_existing_record(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=30,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_returns_movement_instance(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(movement.product, self.product)
        self.assertEqual(movement.quantity, 10)

    def test_receive_with_unit_cost(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=20,
            to_location=self.warehouse,
            unit_cost=Decimal("15.00"),
        )
        self.assertEqual(movement.unit_cost, Decimal("15.00"))

    def test_receive_with_reference_and_notes(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
            reference="PO-12345",
            notes="Received from supplier",
        )
        self.assertEqual(movement.reference, "PO-12345")
        self.assertEqual(movement.notes, "Received from supplier")


# =====================================================================
# Issue
# =====================================================================


class StockServiceIssueTests(StockServiceSetupMixin, TestCase):
    """Test ISSUE movement processing."""

    def test_issue_decrements_stock(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=30,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 70)

    def test_issue_to_zero(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=10,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=10,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 0)

    def test_issue_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=5,
        )
        with self.assertRaises(ValidationError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
            )
        self.assertIn("Insufficient stock", str(ctx.exception.message))

    def test_issue_no_record_raises_error(self):
        with self.assertRaises(ValidationError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=5,
                from_location=self.warehouse,
            )
        self.assertIn("No stock record", str(ctx.exception.message))


# =====================================================================
# Transfer
# =====================================================================


class StockServiceTransferTests(StockServiceSetupMixin, TestCase):
    """Test TRANSFER movement processing."""

    def test_transfer_moves_stock(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        source = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(source.quantity, 60)
        self.assertEqual(dest.quantity, 40)

    def test_transfer_creates_destination_record(self):
        """Destination record is created if it doesn't exist."""
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=20,
            from_location=self.warehouse,
            to_location=self.store,
        )
        self.assertTrue(
            StockRecord.objects.filter(
                product=self.product, location=self.store,
            ).exists()
        )

    def test_transfer_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=5,
        )
        with self.assertRaises(ValidationError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=50,
                from_location=self.warehouse,
                to_location=self.store,
            )

    def test_transfer_conserves_total_quantity(self):
        """Total stock across locations stays the same after transfer."""
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product, location=self.store, quantity=20,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )
        total = sum(
            StockRecord.objects.filter(product=self.product)
            .values_list("quantity", flat=True)
        )
        self.assertEqual(total, 120)


# =====================================================================
# Adjustment
# =====================================================================


class StockServiceAdjustmentTests(StockServiceSetupMixin, TestCase):
    """Test ADJUSTMENT movement processing."""

    def test_positive_adjustment_increments(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=25,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 25)

    def test_negative_adjustment_decrements(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=50,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=15,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 35)

    def test_adjustment_both_locations(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=10,
            from_location=self.warehouse,
            to_location=self.store,
        )
        source = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(source.quantity, 90)
        self.assertEqual(dest.quantity, 10)

    def test_negative_adjustment_insufficient_stock_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=3,
        )
        with self.assertRaises(ValidationError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=10,
                from_location=self.warehouse,
            )


# =====================================================================
# Immutability
# =====================================================================


class StockServiceImmutabilityTests(StockServiceSetupMixin, TestCase):
    """Test that processed movements cannot be modified."""

    def test_cannot_update_processed_movement(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
        )
        movement.quantity = 999
        with self.assertRaises(ValidationError) as ctx:
            movement.save()
        self.assertIn("immutable", str(ctx.exception.message))


# =====================================================================
# Transaction Integrity
# =====================================================================


class StockServiceTransactionTests(StockServiceSetupMixin, TestCase):
    """Test that failed movements don't leave partial state."""

    def test_failed_issue_does_not_create_movement(self):
        """If processing fails, neither movement nor record changes persist."""
        initial_count = self.product.stock_movements.count()
        with self.assertRaises(ValidationError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=999,
                from_location=self.warehouse,
            )
        self.assertEqual(self.product.stock_movements.count(), initial_count)

    def test_failed_transfer_preserves_source_quantity(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=10,
        )
        with self.assertRaises(ValidationError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=50,
                from_location=self.warehouse,
                to_location=self.store,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 10)


# =====================================================================
# Multi-step Sequences
# =====================================================================


class StockServiceSequentialTests(StockServiceSetupMixin, TestCase):
    """Test sequential movements across multiple operations."""

    def test_receive_then_issue_then_transfer(self):
        """Receive → Issue → Transfer sequence produces correct state."""
        # Receive 100 at warehouse
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        # Issue 20 from warehouse
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
        )
        # Transfer 30 warehouse → store
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )

        warehouse_record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        store_record = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(warehouse_record.quantity, 50)  # 100 - 20 - 30
        self.assertEqual(store_record.quantity, 30)

    def test_multiple_receives_accumulate(self):
        for i in range(5):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=10,
                to_location=self.warehouse,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 50)

    def test_movement_count_after_sequence(self):
        """Each process_movement call creates exactly one StockMovement."""
        for qty in [100, 20, 30]:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=qty,
                to_location=self.warehouse,
            )
        self.assertEqual(self.product.stock_movements.count(), 3)
