"""Integration tests for Reservation + Lot integration (T-15).

Covers:
- Lot-specific reservations (create_reservation with stock_lot)
- Lot-agnostic reservation fulfillment (backward compat)
- Lot-aware fulfillment via process_movement_with_lots
- Auto lot assignment using ReservationRule allocation strategy
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.exceptions import InsufficientStockError
from inventory.models import (
    MovementType,
    ReservationStatus,
    StockMovementLot,
    StockRecord,
)
from inventory.models.reservation import AllocationStrategy
from inventory.services.reservation import ReservationService

from ..factories import (
    create_location,
    create_product,
    create_reservation_rule,
    create_stock_lot,
    create_stock_record,
)


class ReservationLotSetupMixin:
    """Shared setup for reservation + lot tests."""

    def setUp(self):
        self.service = ReservationService()
        self.product = create_product(
            sku="RESLOT-001",
            unit_cost=Decimal("10.00"),
            tracking_mode="optional",
        )
        self.warehouse = create_location(name="Res-Lot Warehouse")
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=200,
        )
        self.lot_old = create_stock_lot(
            product=self.product,
            lot_number="LOT-OLD",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date.today() - timedelta(days=30),
        )
        self.lot_new = create_stock_lot(
            product=self.product,
            lot_number="LOT-NEW",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date.today(),
        )


# =====================================================================
# Create lot-specific reservations
# =====================================================================


class CreateLotSpecificReservationTests(ReservationLotSetupMixin, TestCase):
    """Test creating reservations targeting a specific lot."""

    def test_create_reservation_with_lot(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            stock_lot=self.lot_old,
        )
        self.assertEqual(reservation.stock_lot, self.lot_old)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_create_reservation_without_lot_leaves_null(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        self.assertIsNone(reservation.stock_lot)

    def test_lot_specific_reservation_persists_after_refresh(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=25,
            stock_lot=self.lot_new,
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.stock_lot_id, self.lot_new.pk)


# =====================================================================
# Fulfill lot-specific reservations
# =====================================================================


class FulfillLotSpecificReservationTests(ReservationLotSetupMixin, TestCase):
    """Test fulfilling reservations that target a specific lot."""

    def test_fulfill_lot_reservation_creates_lot_aware_movement(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=40,
            stock_lot=self.lot_old,
        )
        movement = self.service.fulfill_reservation(reservation)

        self.assertEqual(movement.movement_type, MovementType.ISSUE)
        self.assertEqual(movement.quantity, 40)

        alloc = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(alloc.stock_lot, self.lot_old)
        self.assertEqual(alloc.quantity, 40)

    def test_fulfill_lot_reservation_decrements_lot_quantity(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
            stock_lot=self.lot_old,
        )
        self.service.fulfill_reservation(reservation)

        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 40)

    def test_fulfill_lot_reservation_decrements_stock_record(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
            stock_lot=self.lot_new,
        )
        self.service.fulfill_reservation(reservation)

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 170)

    def test_fulfill_lot_reservation_sets_fulfilled_status(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=20,
            stock_lot=self.lot_old,
        )
        movement = self.service.fulfill_reservation(reservation)

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)
        self.assertEqual(reservation.fulfilled_movement, movement)

    def test_fulfill_insufficient_lot_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=150,
            stock_lot=self.lot_old,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.fulfill_reservation(reservation)


# =====================================================================
# Fulfill lot-agnostic reservations (backward compat)
# =====================================================================


class FulfillLotAgnosticReservationTests(ReservationLotSetupMixin, TestCase):
    """Fulfilling reservations without a lot uses standard process_movement."""

    def test_fulfill_agnostic_creates_standard_movement(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
        )
        movement = self.service.fulfill_reservation(reservation)

        self.assertEqual(movement.movement_type, MovementType.ISSUE)
        self.assertEqual(movement.quantity, 50)
        self.assertFalse(
            StockMovementLot.objects.filter(stock_movement=movement).exists(),
        )

    def test_fulfill_agnostic_decrements_stock_record(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=45,
        )
        self.service.fulfill_reservation(reservation)

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 155)


# =====================================================================
# Auto lot assignment
# =====================================================================


class AutoAssignLotTests(ReservationLotSetupMixin, TestCase):
    """Test auto_assign_lot picks a lot based on ReservationRule strategy."""

    def test_auto_assign_fifo_picks_oldest_lot(self):
        create_reservation_rule(
            name="FIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            auto_assign_lot=True,
        )
        self.assertEqual(reservation.stock_lot, self.lot_old)

    def test_auto_assign_lifo_picks_newest_lot(self):
        create_reservation_rule(
            name="LIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.LIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            auto_assign_lot=True,
        )
        self.assertEqual(reservation.stock_lot, self.lot_new)

    def test_auto_assign_skips_insufficient_lots(self):
        """When no single lot covers the quantity, stock_lot is None."""
        create_reservation_rule(
            name="FIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=150,
            auto_assign_lot=True,
        )
        self.assertIsNone(reservation.stock_lot)

    def test_auto_assign_without_rule_defaults_fifo(self):
        """No ReservationRule means FIFO is used as default."""
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            auto_assign_lot=True,
        )
        self.assertEqual(reservation.stock_lot, self.lot_old)

    def test_auto_assign_false_does_not_pick_lot(self):
        create_reservation_rule(
            name="FIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            auto_assign_lot=False,
        )
        self.assertIsNone(reservation.stock_lot)

    def test_explicit_lot_overrides_auto_assign(self):
        create_reservation_rule(
            name="FIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            stock_lot=self.lot_new,
            auto_assign_lot=True,
        )
        self.assertEqual(reservation.stock_lot, self.lot_new)


# =====================================================================
# End-to-end: create with auto lot → fulfill → verify lot decremented
# =====================================================================


class EndToEndLotReservationTests(ReservationLotSetupMixin, TestCase):
    """Full lifecycle: create with auto-lot, then fulfill."""

    def test_auto_lot_then_fulfill_decrements_correct_lot(self):
        create_reservation_rule(
            name="FIFO Rule",
            product=self.product,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            auto_assign_lot=True,
        )
        self.assertEqual(reservation.stock_lot, self.lot_old)

        movement = self.service.fulfill_reservation(reservation)

        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 50)

        alloc = StockMovementLot.objects.get(stock_movement=movement)
        self.assertEqual(alloc.stock_lot, self.lot_old)
        self.assertEqual(alloc.quantity, 50)

    def test_cancel_lot_reservation_does_not_touch_lot(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
            stock_lot=self.lot_old,
        )
        self.service.cancel_reservation(reservation)

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

        self.lot_old.refresh_from_db()
        self.assertEqual(self.lot_old.quantity_remaining, 100)
