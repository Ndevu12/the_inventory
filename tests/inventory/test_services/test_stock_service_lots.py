"""Integration tests for lot-aware stock movement processing.

These tests exercise ``StockService.process_movement_with_lots()`` and
verify that StockLot / StockMovementLot records are created, lots are
allocated in FIFO/LIFO order, transfers preserve lot identity, and
tracking-mode enforcement works correctly.
"""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from inventory.exceptions import InsufficientStockError, LotTrackingRequiredError
from inventory.models import MovementType, StockLot, StockMovementLot, StockRecord
from inventory.models.product import TrackingMode
from inventory.services.stock import StockService

from ..factories import create_location, create_product, create_stock_lot, create_stock_record


class LotServiceSetupMixin:
    """Shared setUp for lot-aware StockService tests."""

    def setUp(self):
        self.service = StockService()
        self.product = create_product(
            sku="LOT-SVC-001",
            unit_cost=Decimal("10.00"),
            tracking_mode=TrackingMode.OPTIONAL,
        )
        self.warehouse = create_location(name="Lot Warehouse")
        self.store = create_location(name="Lot Store")


# =====================================================================
# RECEIVE with lot info
# =====================================================================


class LotReceiveTests(LotServiceSetupMixin, TestCase):
    """Test RECEIVE movements with lot information."""

    def test_receive_creates_stock_lot(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-R001",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-R001",
        )
        self.assertEqual(lot.quantity_received, 100)
        self.assertEqual(lot.quantity_remaining, 100)
        self.assertEqual(lot.received_date, date.today())

    def test_receive_creates_stock_movement_lot_link(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="BATCH-R002",
        )
        sml = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(sml.stock_lot.lot_number, "BATCH-R002")
        self.assertEqual(sml.quantity, 50)

    def test_receive_updates_stock_record(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=75,
            to_location=self.warehouse,
            lot_number="BATCH-R003",
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 75)

    def test_receive_with_all_optional_fields(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=200,
            to_location=self.warehouse,
            lot_number="BATCH-R004",
            serial_number="SN-001",
            manufacturing_date=date(2026, 1, 1),
            expiry_date=date(2027, 6, 1),
            unit_cost=Decimal("12.50"),
            reference="PO-LOT-001",
            notes="Test receive with lot",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-R004",
        )
        self.assertEqual(lot.serial_number, "SN-001")
        self.assertEqual(lot.manufacturing_date, date(2026, 1, 1))
        self.assertEqual(lot.expiry_date, date(2027, 6, 1))
        self.assertEqual(movement.unit_cost, Decimal("12.50"))
        self.assertEqual(movement.reference, "PO-LOT-001")

    def test_receive_into_existing_lot_increments_quantities(self):
        """Receiving into the same lot_number adds to existing lot."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-R005",
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="BATCH-R005",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-R005",
        )
        self.assertEqual(lot.quantity_received, 150)
        self.assertEqual(lot.quantity_remaining, 150)

    def test_receive_without_lot_number_creates_no_lot(self):
        """When lot_number is empty, no StockLot is created."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=30,
            to_location=self.warehouse,
        )
        self.assertEqual(StockLot.objects.filter(product=self.product).count(), 0)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 30)


# =====================================================================
# ISSUE with FIFO allocation
# =====================================================================


class LotIssueFIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE movements with FIFO (First In, First Out) allocation."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=300,
        )
        self.lot_old = create_stock_lot(
            product=self.product,
            lot_number="FIFO-OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2025, 1, 1),
        )
        self.lot_mid = create_stock_lot(
            product=self.product,
            lot_number="FIFO-MID",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2025, 6, 1),
        )
        self.lot_new = create_stock_lot(
            product=self.product,
            lot_number="FIFO-NEW",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2026, 1, 1),
        )

    def test_fifo_allocates_oldest_lot_first(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=50,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .select_related("stock_lot")
        )
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].stock_lot.lot_number, "FIFO-OLD")
        self.assertEqual(allocs[0].quantity, 50)

        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 50)

    def test_fifo_spans_multiple_lots(self):
        """Issuing more than one lot holds creates multiple allocations."""
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=150,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .order_by("stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].stock_lot.lot_number, "FIFO-OLD")
        self.assertEqual(allocs[0].quantity, 100)
        self.assertEqual(allocs[1].stock_lot.lot_number, "FIFO-MID")
        self.assertEqual(allocs[1].quantity, 50)

        self.lot_old.refresh_from_db()
        self.lot_mid.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 0)
        self.assertEqual(self.lot_mid.quantity_remaining, 50)

    def test_fifo_allocates_all_three_lots(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=300,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        allocs = StockMovementLot.objects.filter(
            stock_movement=movement,
        ).count()
        self.assertEqual(allocs, 3)

        for lot in [self.lot_old, self.lot_mid, self.lot_new]:
            lot.refresh_from_db()
            self.assertEqual(lot.quantity_remaining, 0)

    def test_fifo_insufficient_lot_quantity_raises_error(self):
        """When lots don't cover the requested quantity, raise error."""
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=400,
                from_location=self.warehouse,
                allocation_strategy="FIFO",
            )

    def test_fifo_insufficient_lot_but_sufficient_stock_raises_error(self):
        """When stock record has enough but lots don't, raise error."""
        create_stock_record(
            product=self.product, location=self.store, quantity=500,
        )
        create_stock_lot(
            product=self.product,
            lot_number="FIFO-EXTRA",
            quantity_received=10,
            quantity_remaining=10,
            received_date=date(2026, 6, 1),
        )
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=500,
                from_location=self.store,
                allocation_strategy="FIFO",
            )
        self.assertIn("Insufficient lot quantity", str(ctx.exception))


# =====================================================================
# ISSUE with LIFO allocation
# =====================================================================


class LotIssueLIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE movements with LIFO (Last In, First Out) allocation."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=250,
        )
        self.lot_old = create_stock_lot(
            product=self.product,
            lot_number="LIFO-OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2025, 1, 1),
        )
        self.lot_mid = create_stock_lot(
            product=self.product,
            lot_number="LIFO-MID",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date(2025, 6, 1),
        )
        self.lot_new = create_stock_lot(
            product=self.product,
            lot_number="LIFO-NEW",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2026, 1, 1),
        )

    def test_lifo_allocates_newest_lot_first(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=60,
            from_location=self.warehouse,
            allocation_strategy="LIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .select_related("stock_lot")
        )
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].stock_lot.lot_number, "LIFO-NEW")
        self.assertEqual(allocs[0].quantity, 60)

        self.lot_new.refresh_from_db()
        self.assertEqual(self.lot_new.quantity_remaining, 40)

    def test_lifo_spans_multiple_lots(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=120,
            from_location=self.warehouse,
            allocation_strategy="LIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .order_by("-stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].stock_lot.lot_number, "LIFO-NEW")
        self.assertEqual(allocs[0].quantity, 100)
        self.assertEqual(allocs[1].stock_lot.lot_number, "LIFO-MID")
        self.assertEqual(allocs[1].quantity, 20)

        self.lot_new.refresh_from_db()
        self.lot_mid.refresh_from_db()
        self.assertEqual(self.lot_new.quantity_remaining, 0)
        self.assertEqual(self.lot_mid.quantity_remaining, 30)


# =====================================================================
# TRANSFER preserves lot identity
# =====================================================================


class LotTransferTests(LotServiceSetupMixin, TestCase):
    """Test TRANSFER movements preserve lot identity."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        self.lot = create_stock_lot(
            product=self.product,
            lot_number="XFER-001",
            quantity_received=200,
            quantity_remaining=200,
            received_date=date(2025, 6, 1),
        )

    def test_transfer_creates_movement_lot_link(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=80,
            from_location=self.warehouse,
            to_location=self.store,
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
        )
        self.assertEqual(len(allocs), 1)
        self.assertEqual(allocs[0].stock_lot.lot_number, "XFER-001")
        self.assertEqual(allocs[0].quantity, 80)

    def test_transfer_does_not_decrement_lot_quantity(self):
        """Transfer relocates stock; lot quantity_remaining is unchanged."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=80,
            from_location=self.warehouse,
            to_location=self.store,
        )
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_remaining, 200)

    def test_transfer_updates_stock_records(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=80,
            from_location=self.warehouse,
            to_location=self.store,
        )
        source = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dest = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(source.quantity, 120)
        self.assertEqual(dest.quantity, 80)


# =====================================================================
# Tracking mode enforcement
# =====================================================================


class TrackingModeRequiredTests(TestCase):
    """Test product with tracking_mode='required' enforces lot info."""

    def setUp(self):
        self.service = StockService()
        self.product = create_product(
            sku="TM-REQ-001",
            tracking_mode=TrackingMode.REQUIRED,
        )
        self.warehouse = create_location(name="TM Warehouse")

    def test_receive_without_lot_raises_lot_tracking_required(self):
        with self.assertRaises(LotTrackingRequiredError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=100,
                to_location=self.warehouse,
            )
        self.assertIn("requires lot tracking", str(ctx.exception))

    def test_receive_with_lot_succeeds(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="REQ-BATCH-001",
        )
        self.assertIsNotNone(movement.pk)
        self.assertTrue(
            StockLot.objects.filter(
                product=self.product, lot_number="REQ-BATCH-001",
            ).exists()
        )


class TrackingModeNoneTests(TestCase):
    """Test product with tracking_mode='none' ignores lot info."""

    def setUp(self):
        self.service = StockService()
        self.product = create_product(
            sku="TM-NONE-001",
            tracking_mode=TrackingMode.NONE,
        )
        self.warehouse = create_location(name="TM None Warehouse")

    def test_lot_info_ignored_for_none_tracking(self):
        """When tracking_mode='none', lot fields are silently ignored."""
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="SHOULD-BE-IGNORED",
        )
        self.assertIsNotNone(movement.pk)
        self.assertFalse(
            StockLot.objects.filter(product=self.product).exists()
        )
        self.assertFalse(
            StockMovementLot.objects.filter(stock_movement=movement).exists()
        )

    def test_no_lot_info_still_works(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=25,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 25)


# =====================================================================
# Concurrent ISSUE (race condition / select_for_update verification)
# =====================================================================


class LotConcurrentIssueTests(LotServiceSetupMixin, TestCase):
    """Verify that concurrent ISSUE movements don't over-allocate lots.

    These tests verify that ``select_for_update`` is used when
    reading lot quantities, preventing two concurrent transactions from
    both reading the same ``quantity_remaining`` and over-decrementing.
    """

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        self.lot = create_stock_lot(
            product=self.product,
            lot_number="RACE-001",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2025, 1, 1),
        )

    def test_select_for_update_used_in_lot_allocation(self):
        """Verify that lot queries use select_for_update for locking."""
        with patch.object(
            StockLot.objects, "select_for_update", wraps=StockLot.objects.select_for_update,
        ) as mock_sfu:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="FIFO",
            )
            mock_sfu.assert_called()

    def test_sequential_issues_dont_over_allocate(self):
        """Two sequential issues that together exceed lot qty: second fails."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=70,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_remaining, 30)

        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="FIFO",
            )

    def test_lot_quantity_correct_after_partial_issues(self):
        """Multiple partial issues correctly decrement lot quantity."""
        for qty in [20, 30, 40]:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=qty,
                from_location=self.warehouse,
                allocation_strategy="FIFO",
            )
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity_remaining, 10)


# =====================================================================
# Backward compatibility
# =====================================================================


class LotBackwardCompatibilityTests(LotServiceSetupMixin, TestCase):
    """Verify original process_movement() is unaffected by lot features."""

    def test_process_movement_without_lots_still_works(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertFalse(
            StockMovementLot.objects.filter(stock_movement=movement).exists()
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 100)

    def test_process_movement_does_not_create_lots(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertEqual(StockLot.objects.filter(product=self.product).count(), 0)


# =====================================================================
# Multi-lot ISSUE spanning all lots
# =====================================================================


class LotIssueSpanningTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE that spans multiple lots creates multiple StockMovementLot."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=175,
        )
        self.lot_a = create_stock_lot(
            product=self.product,
            lot_number="SPAN-A",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date(2025, 1, 1),
        )
        self.lot_b = create_stock_lot(
            product=self.product,
            lot_number="SPAN-B",
            quantity_received=75,
            quantity_remaining=75,
            received_date=date(2025, 6, 1),
        )
        self.lot_c = create_stock_lot(
            product=self.product,
            lot_number="SPAN-C",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date(2026, 1, 1),
        )

    def test_issue_spanning_three_lots_creates_three_records(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=175,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .order_by("stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 3)
        self.assertEqual(allocs[0].quantity, 50)  # lot_a fully consumed
        self.assertEqual(allocs[1].quantity, 75)  # lot_b fully consumed
        self.assertEqual(allocs[2].quantity, 50)  # lot_c fully consumed

        for lot in [self.lot_a, self.lot_b, self.lot_c]:
            lot.refresh_from_db()
            self.assertEqual(lot.quantity_remaining, 0)

    def test_issue_partial_span_leaves_remainder(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=60,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        allocs = list(
            StockMovementLot.objects.filter(stock_movement=movement)
            .order_by("stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].quantity, 50)  # lot_a fully consumed
        self.assertEqual(allocs[1].quantity, 10)  # lot_b partially consumed

        self.lot_a.refresh_from_db()
        self.lot_b.refresh_from_db()
        self.assertEqual(self.lot_a.quantity_remaining, 0)
        self.assertEqual(self.lot_b.quantity_remaining, 65)
