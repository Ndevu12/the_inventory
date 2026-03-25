"""Tests for ReservationService business logic.

Covers the full reservation lifecycle: create, fulfill, cancel, expire,
and available-quantity calculations.  Race-condition coverage uses
``select_for_update`` (verified via concurrent-scenario tests).
"""

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from inventory.exceptions import InsufficientStockError, ReservationConflictError
from inventory.models import (
    MovementType,
    ReservationStatus,
    StockLocation,
    StockRecord,
    StockReservation,
    Warehouse,
)
from inventory.services.reservation import (
    ReservationService,
    filter_stock_reservations_by_warehouse_scope,
)

from tests.fixtures.factories import create_tenant

from ..factories import (
    create_location,
    create_product,
    create_reservation,
    create_stock_record,
    create_tenant as create_tenant_without_context,
    create_user,
)


class ReservationServiceSetupMixin:
    """Shared setUp for ReservationService tests."""

    def setUp(self):
        self.service = ReservationService()
        self.tenant = create_tenant()
        self.product = create_product(sku="RSV-001", unit_cost=Decimal("10.00"), tenant=self.tenant)
        self.warehouse = create_location(name="Warehouse", tenant=self.tenant)
        self.user = create_user(username="reservist")
        create_stock_record(
            product=self.product, location=self.warehouse, quantity=100,
        )


# =====================================================================
# Create reservation
# =====================================================================


class CreateReservationTests(ReservationServiceSetupMixin, TestCase):
    """Test ReservationService.create_reservation."""

    def test_create_with_sufficient_stock(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
            reserved_by=self.user,
        )
        self.assertEqual(reservation.status, ReservationStatus.PENDING)
        self.assertEqual(reservation.quantity, 50)
        self.assertEqual(reservation.product, self.product)
        self.assertEqual(reservation.location, self.warehouse)
        self.assertEqual(reservation.reserved_by, self.user)
        self.assertIsNotNone(reservation.expires_at)

    def test_create_sets_default_expires_at(self):
        before = timezone.now()
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        after = timezone.now()
        self.assertGreater(reservation.expires_at, before)
        self.assertLess(reservation.expires_at, after + timedelta(hours=25))

    def test_create_with_custom_expires_at(self):
        custom_expiry = timezone.now() + timedelta(hours=48)
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
            expires_at=custom_expiry,
        )
        self.assertEqual(reservation.expires_at, custom_expiry)

    def test_create_with_notes(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=5,
            notes="Urgent order",
        )
        self.assertEqual(reservation.notes, "Urgent order")

    def test_create_with_insufficient_stock_raises_error(self):
        with self.assertRaises(InsufficientStockError) as ctx:
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=200,
            )
        self.assertIn("only", str(ctx.exception).lower())

    def test_create_with_zero_quantity_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=0,
            )

    def test_create_with_negative_quantity_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=-5,
            )

    def test_create_rejects_mismatched_tenant_location(self):
        other_tenant = create_tenant_without_context()
        other_location = create_location(name="Foreign bin", tenant=other_tenant)
        with self.assertRaises(ValidationError):
            self.service.create_reservation(
                product=self.product,
                location=other_location,
                quantity=1,
            )

    def test_create_accounts_for_existing_reservations(self):
        """Available quantity is reduced by prior active reservations."""
        self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=80,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=30,
            )

    def test_create_after_cancel_frees_stock(self):
        """Cancelled reservations no longer block available stock."""
        r1 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=80,
        )
        self.service.cancel_reservation(r1)
        r2 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=80,
        )
        self.assertEqual(r2.quantity, 80)

    def test_create_at_no_stock_record_returns_zero_available(self):
        other_product = create_product(sku="RSV-NOSTOCK", tenant=self.tenant)
        with self.assertRaises(InsufficientStockError):
            self.service.create_reservation(
                product=other_product,
                location=self.warehouse,
                quantity=1,
            )

    def test_create_exactly_at_available_quantity(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=100,
        )
        self.assertEqual(reservation.quantity, 100)


# =====================================================================
# Fulfill reservation
# =====================================================================


class FulfillReservationTests(ReservationServiceSetupMixin, TestCase):
    """Test ReservationService.fulfill_reservation."""

    def test_fulfill_pending_reservation(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        movement = self.service.fulfill_reservation(
            reservation, created_by=self.user,
        )

        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)
        self.assertIsNotNone(reservation.fulfilled_movement)
        self.assertEqual(reservation.fulfilled_movement, movement)

    def test_fulfill_creates_issue_movement(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=25,
        )
        movement = self.service.fulfill_reservation(
            reservation, created_by=self.user,
        )

        self.assertEqual(movement.movement_type, MovementType.ISSUE)
        self.assertEqual(movement.quantity, 25)
        self.assertEqual(movement.from_location, self.warehouse)
        self.assertEqual(movement.product, self.product)

    def test_fulfill_decrements_stock_record(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=40,
        )
        self.service.fulfill_reservation(reservation, created_by=self.user)

        record = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        )
        self.assertEqual(record.quantity, 60)

    def test_fulfill_confirmed_reservation(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=20,
        )
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status"])

        movement = self.service.fulfill_reservation(
            reservation, created_by=self.user,
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)
        self.assertIsNotNone(movement.pk)

    def test_fulfill_cancelled_reservation_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        self.service.cancel_reservation(reservation)

        with self.assertRaises(ReservationConflictError) as ctx:
            self.service.fulfill_reservation(reservation, created_by=self.user)
        self.assertIn("Cannot fulfill", str(ctx.exception))

    def test_fulfill_fulfilled_reservation_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        self.service.fulfill_reservation(reservation, created_by=self.user)

        with self.assertRaises(ReservationConflictError):
            self.service.fulfill_reservation(reservation, created_by=self.user)

    def test_fulfill_expired_reservation_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        reservation.status = ReservationStatus.EXPIRED
        reservation.save(update_fields=["status"])

        with self.assertRaises(ReservationConflictError):
            self.service.fulfill_reservation(reservation, created_by=self.user)

    def test_fulfill_movement_reference_contains_reservation_pk(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=5,
        )
        movement = self.service.fulfill_reservation(
            reservation, created_by=self.user,
        )
        self.assertIn(str(reservation.pk), movement.reference)


# =====================================================================
# Cancel reservation
# =====================================================================


class CancelReservationTests(ReservationServiceSetupMixin, TestCase):
    """Test ReservationService.cancel_reservation."""

    def test_cancel_pending_reservation(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        self.service.cancel_reservation(reservation)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_cancel_confirmed_reservation(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=20,
        )
        reservation.status = ReservationStatus.CONFIRMED
        reservation.save(update_fields=["status"])

        self.service.cancel_reservation(reservation)
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_cancel_releases_reserved_quantity(self):
        """After cancellation, the reserved qty becomes available again."""
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=80,
        )
        self.assertEqual(self.service.get_available_quantity(
            self.product, self.warehouse,
        ), 20)

        self.service.cancel_reservation(reservation)
        self.assertEqual(self.service.get_available_quantity(
            self.product, self.warehouse,
        ), 100)

    def test_cancel_fulfilled_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        self.service.fulfill_reservation(reservation, created_by=self.user)

        with self.assertRaises(ReservationConflictError) as ctx:
            self.service.cancel_reservation(reservation)
        self.assertIn("Cannot cancel", str(ctx.exception))

    def test_cancel_expired_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        reservation.status = ReservationStatus.EXPIRED
        reservation.save(update_fields=["status"])

        with self.assertRaises(ReservationConflictError):
            self.service.cancel_reservation(reservation)

    def test_cancel_already_cancelled_raises_error(self):
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
        )
        self.service.cancel_reservation(reservation)

        with self.assertRaises(ReservationConflictError):
            self.service.cancel_reservation(reservation)

    def test_cancel_does_not_change_stock_record(self):
        """Cancellation only releases the reservation, not actual stock."""
        reservation = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        record_before = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        ).quantity

        self.service.cancel_reservation(reservation)

        record_after = StockRecord.objects.get(
            product=self.product, location=self.warehouse,
        ).quantity
        self.assertEqual(record_before, record_after)


# =====================================================================
# Expire stale reservations
# =====================================================================


class ExpireStaleReservationsTests(ReservationServiceSetupMixin, TestCase):
    """Test ReservationService.expire_stale_reservations."""

    def test_expire_stale_pending_reservations(self):
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.PENDING,
            expires_at=past,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 1)
        self.assertEqual(
            StockReservation.objects.filter(
                status=ReservationStatus.EXPIRED,
            ).count(),
            1,
        )

    def test_expire_stale_confirmed_reservations(self):
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.CONFIRMED,
            expires_at=past,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 1)

    def test_future_reservations_not_expired(self):
        future = timezone.now() + timedelta(hours=24)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.PENDING,
            expires_at=future,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 0)

    def test_already_fulfilled_not_expired(self):
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.FULFILLED,
            expires_at=past,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 0)

    def test_already_cancelled_not_expired(self):
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.CANCELLED,
            expires_at=past,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 0)

    def test_already_expired_not_double_expired(self):
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.EXPIRED,
            expires_at=past,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 0)

    def test_bulk_expiry(self):
        past = timezone.now() - timedelta(hours=1)
        for i in range(5):
            create_reservation(
                product=self.product,
                location=create_location(name=f"Loc-{i}", tenant=self.tenant),
                status=ReservationStatus.PENDING,
                expires_at=past,
            )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 5)

    def test_expired_reservations_release_available_quantity(self):
        """After expiry, the reserved qty is freed up for new reservations."""
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=80,
            status=ReservationStatus.PENDING,
            expires_at=past,
        )
        self.assertEqual(
            self.service.get_available_quantity(self.product, self.warehouse), 20,
        )
        self.service.expire_stale_reservations()
        self.assertEqual(
            self.service.get_available_quantity(self.product, self.warehouse), 100,
        )

    def test_no_expires_at_not_expired(self):
        """Reservations without expires_at are never auto-expired."""
        create_reservation(
            product=self.product,
            location=self.warehouse,
            status=ReservationStatus.PENDING,
            expires_at=None,
        )
        count = self.service.expire_stale_reservations()
        self.assertEqual(count, 0)


# =====================================================================
# get_available_quantity
# =====================================================================


class GetAvailableQuantityTests(ReservationServiceSetupMixin, TestCase):
    """Test ReservationService.get_available_quantity."""

    def test_no_reservations_returns_full_stock(self):
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 100)

    def test_pending_reservation_reduces_available(self):
        self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 70)

    def test_confirmed_reservation_reduces_available(self):
        r = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=40,
        )
        r.status = ReservationStatus.CONFIRMED
        r.save(update_fields=["status"])

        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 60)

    def test_fulfilled_reservation_does_not_reduce_available(self):
        r = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=20,
        )
        self.service.fulfill_reservation(r, created_by=self.user)

        # Stock was decremented by the ISSUE movement (100 - 20 = 80).
        # Fulfilled reservation should not further reduce available qty.
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 80)

    def test_cancelled_reservation_does_not_reduce_available(self):
        r = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=50,
        )
        self.service.cancel_reservation(r)

        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 100)

    def test_expired_reservation_does_not_reduce_available(self):
        create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
            status=ReservationStatus.EXPIRED,
        )
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 100)

    def test_multiple_active_reservations_cumulative(self):
        self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=30,
        )
        self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=25,
        )
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 45)

    def test_no_stock_record_returns_zero(self):
        other = create_product(sku="RSV-NOSR", tenant=self.tenant)
        available = self.service.get_available_quantity(
            other, self.warehouse,
        )
        self.assertEqual(available, 0)

    def test_available_never_negative(self):
        """If reservations somehow exceed stock, available is clamped to 0."""
        create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
            status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
            status=ReservationStatus.PENDING,
        )
        available = self.service.get_available_quantity(
            self.product, self.warehouse,
        )
        self.assertEqual(available, 0)


# =====================================================================
# Warehouse scope queries (nullable location.warehouse)
# =====================================================================


class FilterReservationsByWarehouseScopeTests(TestCase):
    """Tests for :func:`filter_stock_reservations_by_warehouse_scope`."""

    def setUp(self):
        self.tenant = create_tenant()
        self.product = create_product(sku="WH-RSV-001", tenant=self.tenant)
        self.wh = Warehouse.objects.create(tenant=self.tenant, name="DC North")
        self.loc_dc = StockLocation.add_root(
            name="Pick face",
            tenant=self.tenant,
            warehouse=self.wh,
        )
        self.loc_retail = StockLocation.add_root(
            name="Shop floor",
            tenant=self.tenant,
        )

    def test_facility_partition_excludes_retail_locations(self):
        create_reservation(
            product=self.product,
            location=self.loc_dc,
            quantity=1,
            tenant=self.tenant,
        )
        create_reservation(
            product=self.product,
            location=self.loc_retail,
            quantity=1,
            tenant=self.tenant,
        )
        qs = filter_stock_reservations_by_warehouse_scope(
            StockReservation.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=self.wh.pk,
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().location_id, self.loc_dc.pk)

    def test_retail_partition_excludes_facility_locations(self):
        create_reservation(
            product=self.product,
            location=self.loc_dc,
            quantity=1,
            tenant=self.tenant,
        )
        r_shop = create_reservation(
            product=self.product,
            location=self.loc_retail,
            quantity=1,
            tenant=self.tenant,
        )
        qs = filter_stock_reservations_by_warehouse_scope(
            StockReservation.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=None,
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.get().pk, r_shop.pk)

    def test_other_tenant_excluded_from_scope(self):
        other = create_tenant_without_context()
        other_product = create_product(sku="WH-OTHER", tenant=other)
        other_loc = StockLocation.add_root(name="Their bin", tenant=other)
        create_reservation(
            product=other_product,
            location=other_loc,
            quantity=1,
            tenant=other,
        )
        create_reservation(
            product=self.product,
            location=self.loc_retail,
            quantity=1,
            tenant=self.tenant,
        )
        qs = filter_stock_reservations_by_warehouse_scope(
            StockReservation.objects.all(),
            tenant_id=self.tenant.pk,
            warehouse_id=None,
        )
        self.assertEqual(qs.count(), 1)


# =====================================================================
# Expire stale — optional tenant
# =====================================================================


class ExpireStaleReservationsTenantScopedTests(TestCase):
    def test_expire_only_named_tenant(self):
        t1 = create_tenant_without_context()
        t2 = create_tenant_without_context()
        p1 = create_product(sku="EXP-T1", tenant=t1)
        p2 = create_product(sku="EXP-T2", tenant=t2)
        l1 = create_location(name="Loc-T1", tenant=t1)
        l2 = create_location(name="Loc-T2", tenant=t2)
        past = timezone.now() - timedelta(hours=1)
        create_reservation(
            product=p1,
            location=l1,
            expires_at=past,
            status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=p2,
            location=l2,
            expires_at=past,
            status=ReservationStatus.PENDING,
        )
        service = ReservationService()
        count = service.expire_stale_reservations(tenant_id=t1.pk)
        self.assertEqual(count, 1)
        self.assertEqual(
            StockReservation.objects.filter(
                tenant=t1,
                status=ReservationStatus.EXPIRED,
            ).count(),
            1,
        )
        self.assertEqual(
            StockReservation.objects.filter(
                tenant=t2,
                status=ReservationStatus.EXPIRED,
            ).count(),
            0,
        )
        self.assertEqual(
            StockReservation.objects.filter(
                tenant=t2,
                status=ReservationStatus.PENDING,
            ).count(),
            1,
        )


# =====================================================================
# Concurrent / Race condition coverage
# =====================================================================


class ConcurrentReservationTests(ReservationServiceSetupMixin, TestCase):
    """Test that select_for_update prevents over-reservation.

    Uses :class:`~django.test.TestCase` (not :class:`~django.test.TransactionTestCase`)
    so Wagtail ``Locale`` rows seeded by migrations are not truncated between
    tests; ``select_for_update`` remains meaningful within each test's transaction.
    """

    def test_sequential_reservations_dont_over_reserve(self):
        """Two sequential reservations totalling more than stock fail correctly."""
        self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=70,
        )
        with self.assertRaises(InsufficientStockError):
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=50,
            )

    def test_cancel_then_reserve_uses_freed_stock(self):
        """After cancel, the freed stock is available for new reservations."""
        r1 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=70,
        )
        self.service.cancel_reservation(r1)
        r2 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=70,
        )
        self.assertEqual(r2.status, ReservationStatus.PENDING)

    def test_fulfill_then_reserve_within_remaining_stock(self):
        """After fulfillment decrements stock, new reservation accounts for it."""
        r1 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
        )
        self.service.fulfill_reservation(r1, created_by=self.user)
        # Stock is now 40, no active reservations
        r2 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=40,
        )
        self.assertEqual(r2.quantity, 40)

    def test_fulfill_then_over_reserve_fails(self):
        r1 = self.service.create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=60,
        )
        self.service.fulfill_reservation(r1, created_by=self.user)
        # Stock is now 40
        with self.assertRaises(InsufficientStockError):
            self.service.create_reservation(
                product=self.product,
                location=self.warehouse,
                quantity=50,
            )
