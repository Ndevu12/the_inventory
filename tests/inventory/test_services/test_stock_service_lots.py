"""Lot-aware StockService tests: RECEIVE, ISSUE (FIFO/LIFO/MANUAL), TRANSFER, ADJUSTMENT.

Tests lot tracking functionality including allocation strategies, tracking mode
enforcement, and end-to-end lot sequences.
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.exceptions import InsufficientStockError, LotTrackingRequiredError
from inventory.models import (
    MovementType,
    StockLot,
    StockMovementLot,
    StockRecord,
)
from inventory.services.stock import StockService

from ..factories import (
    create_location,
    create_product,
    create_stock_lot,
    create_stock_record,
    create_tenant,
)


class LotServiceSetupMixin:
    """Shared setUp for lot-aware StockService tests."""

    def setUp(self):
        super().setUp()
        self.tenant = create_tenant()
        self.product = create_product(
            sku="LOT-001",
            unit_cost=Decimal("10.00"),
            tracking_mode="optional",
            tenant=self.tenant,
        )
        self.warehouse = create_location(name="Lot Warehouse", tenant=self.tenant)
        self.store = create_location(name="Lot Store", tenant=self.tenant)
        self.service = StockService()


class LotReceiveTests(LotServiceSetupMixin, TestCase):
    """Test RECEIVE via process_movement_with_lots."""

    def test_receive_creates_lot_and_link(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-001",
        )
        self.assertEqual(lot.quantity_received, 100)
        self.assertEqual(lot.quantity_remaining, 100)
        self.assertEqual(lot.received_date, date.today())

        sml = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(sml.stock_lot, lot)
        self.assertEqual(sml.quantity, 100)

    def test_receive_increments_existing_lot(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="BATCH-001",
        )
        lot = StockLot.objects.get(
            product=self.product, lot_number="BATCH-001",
        )
        self.assertEqual(lot.quantity_received, 150)
        self.assertEqual(lot.quantity_remaining, 150)
        self.assertEqual(StockMovementLot.objects.count(), 2)

    def test_receive_stores_serial_and_dates(self):
        mfg = date(2026, 1, 1)
        exp = date(2027, 1, 1)
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
            lot_number="SN-LOT",
            serial_number="SN-12345",
            manufacturing_date=mfg,
            expiry_date=exp,
        )
        lot = StockLot.objects.get(lot_number="SN-LOT")
        self.assertEqual(lot.serial_number, "SN-12345")
        self.assertEqual(lot.manufacturing_date, mfg)
        self.assertEqual(lot.expiry_date, exp)

    def test_receive_without_lot_number_skips_lot_creation(self):
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 50)

    def test_receive_updates_stock_record(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=75,
            to_location=self.warehouse,
            lot_number="BATCH-X",
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 75)


class LotIssueFIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with FIFO allocation."""

    def _receive_lots(self):
        """Create three lots with staggered received_dates."""
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=250,
        )
        self.lot_old = create_stock_lot(
            product=self.product,
            lot_number="OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=30),
        )
        self.lot_mid = create_stock_lot(
            product=self.product,
            lot_number="MID",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=15),
        )
        self.lot_new = create_stock_lot(
            product=self.product,
            lot_number="NEW",
            quantity_received=50,
            quantity_remaining=50,
            received_date=today,
        )

    def test_fifo_allocates_from_oldest_first(self):
        self._receive_lots()
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=80,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 20)

        allocs = StockMovementLot.objects.filter(stock_movement=movement)
        self.assertEqual(allocs.count(), 1)
        self.assertEqual(allocs.first().stock_lot, self.lot_old)
        self.assertEqual(allocs.first().quantity, 80)

    def test_fifo_spans_multiple_lots(self):
        self._receive_lots()
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=150,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )
        self.lot_old.refresh_from_db()
        self.lot_mid.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 0)
        self.assertEqual(self.lot_mid.quantity_remaining, 50)

        allocs = list(
            StockMovementLot.objects
            .filter(stock_movement=movement)
            .order_by("stock_lot__received_date")
        )
        self.assertEqual(len(allocs), 2)
        self.assertEqual(allocs[0].stock_lot, self.lot_old)
        self.assertEqual(allocs[0].quantity, 100)
        self.assertEqual(allocs[1].stock_lot, self.lot_mid)
        self.assertEqual(allocs[1].quantity, 50)

    def test_fifo_insufficient_lot_quantity_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=999,
        )
        create_stock_lot(
            product=self.product,
            lot_number="SMALL",
            quantity_received=10,
            quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
            )
        self.assertIn("lot quantity", str(ctx.exception))

    def test_fifo_decrements_stock_record(self):
        self._receive_lots()
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=60,
            from_location=self.warehouse,
        )
        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 190)


class LotIssueLIFOTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with LIFO allocation."""

    def test_lifo_allocates_from_newest_first(self):
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_old = create_stock_lot(
            product=self.product,
            lot_number="OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today - timedelta(days=30),
        )
        lot_new = create_stock_lot(
            product=self.product,
            lot_number="NEW",
            quantity_received=100,
            quantity_remaining=100,
            received_date=today,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=80,
            from_location=self.warehouse,
            allocation_strategy="LIFO",
        )
        lot_new.refresh_from_db()
        lot_old.refresh_from_db()
        self.assertEqual(lot_new.quantity_remaining, 20)
        self.assertEqual(lot_old.quantity_remaining, 100)

        alloc = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(alloc.stock_lot, lot_new)


class LotIssueManualTests(LotServiceSetupMixin, TestCase):
    """Test ISSUE with MANUAL allocation strategy."""

    def test_manual_allocation(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_a = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        lot_b = create_stock_lot(
            product=self.product, lot_number="B",
            quantity_received=100, quantity_remaining=100,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=70,
            from_location=self.warehouse,
            allocation_strategy="MANUAL",
            manual_lot_allocations=[
                {"lot_id": lot_a.pk, "quantity": 30},
                {"lot_id": lot_b.pk, "quantity": 40},
            ],
        )
        lot_a.refresh_from_db()
        lot_b.refresh_from_db()
        self.assertEqual(lot_a.quantity_remaining, 70)
        self.assertEqual(lot_b.quantity_remaining, 60)

        allocs = StockMovementLot.objects.filter(stock_movement=movement)
        self.assertEqual(allocs.count(), 2)

    def test_manual_total_mismatch_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        with self.assertRaises(ValueError) as ctx:
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
                manual_lot_allocations=[
                    {"lot_id": lot.pk, "quantity": 30},
                ],
            )
        self.assertIn("does not match", str(ctx.exception))

    def test_manual_insufficient_lot_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=10, quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=50,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
                manual_lot_allocations=[
                    {"lot_id": lot.pk, "quantity": 50},
                ],
            )

    def test_manual_requires_allocations(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="A",
            quantity_received=100, quantity_remaining=100,
        )
        with self.assertRaises(ValueError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ISSUE,
                quantity=10,
                from_location=self.warehouse,
                allocation_strategy="MANUAL",
            )


class LotTransferTests(LotServiceSetupMixin, TestCase):
    """Test TRANSFER preserves lot identity (no quantity_remaining change)."""

    def test_transfer_preserves_lot_quantity_remaining(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 100)

    def test_transfer_creates_movement_lot_entries(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        movement = self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        sml = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(sml.stock_lot, lot)
        self.assertEqual(sml.quantity, 40)

    def test_transfer_updates_stock_records(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="T-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
        )
        src = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        dst = StockRecord.objects.get(
            product=self.product, location=self.store,
        )
        self.assertEqual(src.quantity, 70)
        self.assertEqual(dst.quantity, 30)


class LotAdjustmentTests(LotServiceSetupMixin, TestCase):
    """Test ADJUSTMENT with lot operations."""

    def test_negative_adjustment_targets_specific_lot(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        lot = create_stock_lot(
            product=self.product, lot_number="ADJ-LOT",
            quantity_received=100, quantity_remaining=100,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=25,
            from_location=self.warehouse,
            lot_number="ADJ-LOT",
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 75)

    def test_negative_adjustment_fifo_when_no_lot_number(self):
        today = date.today()
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        lot_old = create_stock_lot(
            product=self.product, lot_number="OLD",
            quantity_received=100, quantity_remaining=100,
            received_date=today - timedelta(days=10),
        )
        lot_new = create_stock_lot(
            product=self.product, lot_number="NEW",
            quantity_received=100, quantity_remaining=100,
            received_date=today,
        )
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=50,
            from_location=self.warehouse,
        )
        lot_old.refresh_from_db()
        lot_new.refresh_from_db()
        self.assertEqual(lot_old.quantity_remaining, 50)
        self.assertEqual(lot_new.quantity_remaining, 100)

    def test_positive_adjustment_creates_lot(self):
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=50,
            to_location=self.warehouse,
            lot_number="ADJ-NEW",
        )
        lot = StockLot.objects.get(lot_number="ADJ-NEW")
        self.assertEqual(lot.quantity_received, 50)
        self.assertEqual(lot.quantity_remaining, 50)

    def test_adjustment_insufficient_specific_lot_raises_error(self):
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )
        create_stock_lot(
            product=self.product, lot_number="SMALL",
            quantity_received=10, quantity_remaining=10,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.process_movement_with_lots(
                product=self.product,
                movement_type=MovementType.ADJUSTMENT,
                quantity=50,
                from_location=self.warehouse,
                lot_number="SMALL",
            )


class TrackingModeTests(TestCase):
    """Test tracking_mode enforcement."""

    def setUp(self):
        super().setUp()
        self.tenant = create_tenant()
        self.warehouse = create_location(name="TM Warehouse", tenant=self.tenant)
        self.service = StockService()

    def test_tracking_none_ignores_lot_info(self):
        product = create_product(
            sku="TM-NONE", tracking_mode="none", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="IGNORED",
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)
        self.assertEqual(StockMovementLot.objects.count(), 0)

    def test_tracking_required_without_lot_raises_error(self):
        product = create_product(
            sku="TM-REQ", tracking_mode="required", tenant=self.tenant,
        )
        with self.assertRaises(LotTrackingRequiredError) as ctx:
            self.service.process_movement_with_lots(
                product=product,
                movement_type=MovementType.RECEIVE,
                quantity=100,
                to_location=self.warehouse,
            )
        self.assertIn("requires lot tracking", str(ctx.exception))

    def test_tracking_required_with_lot_succeeds(self):
        product = create_product(
            sku="TM-REQ-OK", tracking_mode="required", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="REQ-LOT",
        )
        self.assertIsNotNone(movement.pk)
        self.assertTrue(
            StockLot.objects.filter(lot_number="REQ-LOT").exists(),
        )

    def test_tracking_optional_creates_lot_when_provided(self):
        product = create_product(
            sku="TM-OPT", tracking_mode="optional", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            lot_number="OPT-LOT",
        )
        self.assertIsNotNone(movement.pk)
        self.assertTrue(
            StockLot.objects.filter(lot_number="OPT-LOT").exists(),
        )

    def test_tracking_optional_skips_lot_when_not_provided(self):
        product = create_product(
            sku="TM-OPT-SKIP", tracking_mode="optional", tenant=self.tenant,
        )
        movement = self.service.process_movement_with_lots(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        self.assertIsNotNone(movement.pk)
        self.assertEqual(StockLot.objects.count(), 0)


class LotSequenceTests(LotServiceSetupMixin, TestCase):
    """Test multi-step lot-aware movement sequences."""

    def test_receive_then_fifo_issue(self):
        """Receive into lots, then FIFO issue draws from oldest."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="FIRST",
        )
        first_lot = StockLot.objects.get(lot_number="FIRST")
        first_lot.received_date = date.today() - timedelta(days=10)
        first_lot.save(update_fields=["received_date"])

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="SECOND",
        )

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=120,
            from_location=self.warehouse,
            allocation_strategy="FIFO",
        )

        first_lot.refresh_from_db()
        second_lot = StockLot.objects.get(lot_number="SECOND")
        self.assertEqual(first_lot.quantity_remaining, 0)
        self.assertEqual(second_lot.quantity_remaining, 80)

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 80)

    def test_receive_transfer_then_issue_preserves_lots(self):
        """Transfer doesn't consume lots; subsequent issue still can."""
        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            lot_number="LOT-A",
        )
        lot = StockLot.objects.get(lot_number="LOT-A")

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=40,
            from_location=self.warehouse,
            to_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 100)

        self.service.process_movement_with_lots(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=30,
            from_location=self.store,
        )
        lot.refresh_from_db()
        self.assertEqual(lot.quantity_remaining, 70)
