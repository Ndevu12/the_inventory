"""Basic StockService movement tests: RECEIVE, ISSUE, TRANSFER, ADJUSTMENT.

Also includes capacity enforcement, immutability, transaction integrity,
and sequential movement tests.
"""

from decimal import Decimal

from django.test import TestCase

from inventory.exceptions import (
    InsufficientStockError,
    LocationCapacityExceededError,
    MovementImmutableError,
)
from inventory.models import MovementType, StockRecord
from inventory.services.stock import StockService

from ..factories import create_location, create_product, create_stock_record, create_tenant


class StockServiceSetupMixin:
    """Shared setUp for StockService tests."""

    def setUp(self):
        """Create test fixtures and service instance."""
        super().setUp()
        self.tenant = create_tenant()
        self.product = create_product(
            sku="SVC-001",
            unit_cost=Decimal("10.00"),
            tenant=self.tenant,
        )
        self.warehouse = create_location(name="Warehouse", tenant=self.tenant)
        self.store = create_location(name="Store", tenant=self.tenant)
        self.service = StockService()


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
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
            )
        self.assertIn("Insufficient stock", str(ctx.exception))

    def test_issue_no_record_raises_error(self):
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=5,
                from_location=self.warehouse,
            )
        self.assertIn("No stock record", str(ctx.exception))


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
        with self.assertRaises(InsufficientStockError):
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
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=10,
                from_location=self.warehouse,
            )


class StockServiceCapacityTests(TestCase):
    """Test that StockService prevents exceeding location capacity."""

    def setUp(self):
        super().setUp()
        self.tenant = create_tenant()
        self.product = create_product(sku="CAP-SVC-001", tenant=self.tenant)
        self.limited = create_location(
            name="Limited Bin", max_capacity=100, tenant=self.tenant,
        )
        self.unlimited = create_location(
            name="Unlimited Warehouse", tenant=self.tenant,
        )
        self.service = StockService()

    def test_receive_within_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_at_exact_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 100)

    def test_receive_exceeding_capacity_raises_error(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError) as ctx:
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=30,
                to_location=self.limited,
            )
        self.assertIn("cannot accept", str(ctx.exception))

    def test_receive_unlimited_location_always_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=999999,
            to_location=self.unlimited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(record.quantity, 999999)

    def test_receive_capacity_check_is_atomic(self):
        """Failed receive should not partially update stock."""
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=90,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=20,
                to_location=self.limited,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 90)

    def test_transfer_within_dest_capacity_succeeds(self):
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=50,
            from_location=self.unlimited,
            to_location=self.limited,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(dest.quantity, 50)

    def test_transfer_exceeding_dest_capacity_raises_error(self):
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=150,
                from_location=self.unlimited,
                to_location=self.limited,
            )

    def test_transfer_capacity_failure_preserves_source(self):
        """Source stock must not change when destination rejects."""
        create_stock_record(
            product=self.product, location=self.unlimited, quantity=200,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.TRANSFER,
                quantity=150,
                from_location=self.unlimited,
                to_location=self.limited,
            )
        source = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(source.quantity, 200)

    def test_positive_adjustment_within_capacity_succeeds(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=100,
            to_location=self.limited,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.limited,
        )
        self.assertEqual(record.quantity, 100)

    def test_positive_adjustment_exceeding_capacity_raises_error(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=80,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=30,
                to_location=self.limited,
            )

    def test_capacity_accounts_for_all_products(self):
        """Location capacity is shared across all products stored there."""
        p2 = create_product(sku="CAP-SVC-002", tenant=self.tenant)
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=60,
            to_location=self.limited,
        )
        self.service.process_movement(
            product=p2,
            movement_type=MovementType.RECEIVE,
            quantity=30,
            to_location=self.limited,
        )
        with self.assertRaises(LocationCapacityExceededError):
            self.service.process_movement(
                product=p2,
                movement_type=MovementType.RECEIVE,
                quantity=20,
                to_location=self.limited,
            )

    def test_null_capacity_allows_unlimited_stock(self):
        """Existing locations with null max_capacity remain unlimited."""
        self.assertIsNone(self.unlimited.max_capacity)
        for _ in range(5):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=10000,
                to_location=self.unlimited,
            )
        record = StockRecord.objects.get(
            product=self.product, location=self.unlimited,
        )
        self.assertEqual(record.quantity, 50000)


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
        with self.assertRaises(MovementImmutableError) as ctx:
            movement.save()
        self.assertIn("immutable", str(ctx.exception))


class StockServiceTransactionTests(StockServiceSetupMixin, TestCase):
    """Test that failed movements don't leave partial state."""

    def test_failed_issue_does_not_create_movement(self):
        """If processing fails, neither movement nor record changes persist."""
        initial_count = self.product.stock_movements.count()
        with self.assertRaises(InsufficientStockError):
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
        with self.assertRaises(InsufficientStockError):
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


class StockServiceSequentialTests(StockServiceSetupMixin, TestCase):
    """Test sequential movements across multiple operations."""

    def test_receive_then_issue_then_transfer(self):
        """Receive → Issue → Transfer sequence produces correct state."""
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
        )
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
        self.assertEqual(warehouse_record.quantity, 50)
        self.assertEqual(store_record.quantity, 30)

    def test_multiple_receives_accumulate(self):
        for _ in range(5):
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


class BackwardCompatibilityTests(StockServiceSetupMixin, TestCase):
    """Ensure process_movement() is unchanged alongside the new method."""

    def test_process_movement_still_works(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)

    def test_process_movement_creates_no_lot_entries(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        from inventory.models import StockLot, StockMovementLot
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)
