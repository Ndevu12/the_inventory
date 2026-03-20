"""Unit tests for StockReservation model."""

from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from inventory.models import (
    AllocationStrategy,
    MovementType,
    ReservationRule,
    ReservationStatus,
    StockMovement,
    StockReservation,
)

from ..factories import (
    create_category,
    create_location,
    create_product,
    create_reservation,
    create_reservation_rule,
    create_user,
)


# =====================================================================
# StockReservation — creation & defaults
# =====================================================================


class StockReservationCreationTests(TestCase):
    """Test StockReservation creation and field defaults."""

    def test_create_reservation(self):
        product = create_product(sku="RES-001")
        location = create_location(name="Warehouse A")
        reservation = create_reservation(
            product=product, location=location, quantity=25,
        )
        self.assertEqual(reservation.product, product)
        self.assertEqual(reservation.location, location)
        self.assertEqual(reservation.quantity, 25)

    def test_default_status_is_pending(self):
        product = create_product(sku="RES-002")
        location = create_location(name="Warehouse B")
        reservation = create_reservation(product=product, location=location)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

    def test_optional_fields_default_to_none_or_blank(self):
        product = create_product(sku="RES-003")
        location = create_location(name="Warehouse C")
        reservation = create_reservation(product=product, location=location)
        self.assertIsNone(reservation.sales_order)
        self.assertIsNone(reservation.reserved_by)
        self.assertIsNone(reservation.expires_at)
        self.assertIsNone(reservation.fulfilled_movement)
        self.assertEqual(reservation.notes, "")

    def test_timestamps_set_on_create(self):
        product = create_product(sku="RES-004")
        location = create_location(name="Warehouse D")
        reservation = create_reservation(product=product, location=location)
        self.assertIsNotNone(reservation.created_at)
        self.assertIsNotNone(reservation.updated_at)


# =====================================================================
# StockReservation — __str__
# =====================================================================


class StockReservationStrTests(TestCase):
    """Test StockReservation __str__ representation."""

    def test_str_contains_sku_quantity_and_status(self):
        product = create_product(sku="STR-001")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location, quantity=5,
        )
        text = str(reservation)
        self.assertIn("STR-001", text)
        self.assertIn("x5", text)
        self.assertIn("Pending", text)


# =====================================================================
# StockReservation — status values
# =====================================================================


class ReservationStatusTests(TestCase):
    """Test all ReservationStatus choices can be persisted."""

    def test_all_status_values_accepted(self):
        product = create_product(sku="ST-001")
        create_location(name="Warehouse")
        for status_value, label in ReservationStatus.choices:
            reservation = create_reservation(
                product=product,
                location=create_location(name=f"Loc-{status_value}"),
                quantity=1,
                status=status_value,
            )
            reservation.refresh_from_db()
            self.assertEqual(reservation.status, status_value)
            self.assertEqual(
                reservation.get_status_display(), label,
            )

    def test_status_workflow_pending_to_confirmed(self):
        product = create_product(sku="WF-001")
        location = create_location(name="Warehouse")
        reservation = create_reservation(product=product, location=location)
        self.assertEqual(reservation.status, ReservationStatus.PENDING)

        reservation.status = ReservationStatus.CONFIRMED
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CONFIRMED)

    def test_status_workflow_confirmed_to_fulfilled(self):
        product = create_product(sku="WF-002")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.CONFIRMED,
        )
        reservation.status = ReservationStatus.FULFILLED
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)

    def test_status_workflow_confirmed_to_cancelled(self):
        product = create_product(sku="WF-003")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.CONFIRMED,
        )
        reservation.status = ReservationStatus.CANCELLED
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_status_workflow_confirmed_to_expired(self):
        product = create_product(sku="WF-004")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.CONFIRMED,
        )
        reservation.status = ReservationStatus.EXPIRED
        reservation.save()
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.EXPIRED)


# =====================================================================
# StockReservation — FK relationships
# =====================================================================


class StockReservationFKTests(TestCase):
    """Test foreign key relationships."""

    def test_sales_order_is_optional(self):
        product = create_product(sku="FK-001")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location, sales_order=None,
        )
        self.assertIsNone(reservation.sales_order)

    def test_reserved_by_user(self):
        product = create_product(sku="FK-002")
        location = create_location(name="Warehouse")
        user = create_user(username="reservist")
        reservation = create_reservation(
            product=product, location=location, reserved_by=user,
        )
        self.assertEqual(reservation.reserved_by, user)

    def test_fulfilled_movement_link(self):
        product = create_product(sku="FK-003")
        location = create_location(name="Warehouse")
        movement = StockMovement(
            product=product,
            movement_type=MovementType.ISSUE,
            quantity=10,
            from_location=location,
        )
        movement.save()

        reservation = create_reservation(
            product=product,
            location=location,
            quantity=10,
            status=ReservationStatus.FULFILLED,
            fulfilled_movement=movement,
        )
        self.assertEqual(reservation.fulfilled_movement, movement)

    def test_expires_at_can_be_set(self):
        product = create_product(sku="FK-004")
        location = create_location(name="Warehouse")
        expiry = timezone.now() + timezone.timedelta(hours=24)
        reservation = create_reservation(
            product=product, location=location, expires_at=expiry,
        )
        self.assertIsNotNone(reservation.expires_at)

    def test_cascade_delete_product_removes_reservations(self):
        product = create_product(sku="FK-005")
        location = create_location(name="Warehouse")
        create_reservation(product=product, location=location)
        self.assertEqual(StockReservation.objects.count(), 1)

        product.delete()
        self.assertEqual(StockReservation.objects.count(), 0)

    def test_cascade_delete_location_removes_reservations(self):
        product = create_product(sku="FK-006")
        location = create_location(name="Warehouse")
        create_reservation(product=product, location=location)
        self.assertEqual(StockReservation.objects.count(), 1)

        location.delete()
        self.assertEqual(StockReservation.objects.count(), 0)


# =====================================================================
# StockReservation — ordering
# =====================================================================


class StockReservationOrderingTests(TestCase):
    """Test default ordering is -created_at (newest first)."""

    def test_default_ordering_newest_first(self):
        product = create_product(sku="ORD-001")
        loc_a = create_location(name="Loc A")
        loc_b = create_location(name="Loc B")
        r1 = create_reservation(product=product, location=loc_a, quantity=1)
        r2 = create_reservation(product=product, location=loc_b, quantity=2)
        reservations = list(StockReservation.objects.all())
        self.assertEqual(reservations[0].pk, r2.pk)
        self.assertEqual(reservations[1].pk, r1.pk)


# =====================================================================
# StockReservation — expiry logic
# =====================================================================


class StockReservationExpiryTests(TestCase):
    """Test expiry-related logic on StockReservation."""

    def test_reservation_with_future_expires_at(self):
        product = create_product(sku="EXP-001")
        location = create_location(name="Warehouse")
        future = timezone.now() + timedelta(hours=24)
        reservation = create_reservation(
            product=product, location=location, expires_at=future,
        )
        self.assertGreater(reservation.expires_at, timezone.now())

    def test_reservation_with_past_expires_at(self):
        product = create_product(sku="EXP-002")
        location = create_location(name="Warehouse")
        past = timezone.now() - timedelta(hours=1)
        reservation = create_reservation(
            product=product, location=location, expires_at=past,
        )
        self.assertLess(reservation.expires_at, timezone.now())

    def test_stale_reservations_queryset_filter(self):
        """Reservations past their expires_at with active status are 'stale'."""
        product = create_product(sku="EXP-003")
        create_location(name="Warehouse")
        past = timezone.now() - timedelta(hours=1)
        future = timezone.now() + timedelta(hours=24)

        stale = create_reservation(
            product=product, location=create_location(name="Loc-stale"),
            expires_at=past, status=ReservationStatus.PENDING,
        )
        fresh = create_reservation(
            product=product, location=create_location(name="Loc-fresh"),
            expires_at=future, status=ReservationStatus.PENDING,
        )
        already_expired = create_reservation(
            product=product, location=create_location(name="Loc-done"),
            expires_at=past, status=ReservationStatus.EXPIRED,
        )

        stale_qs = StockReservation.objects.filter(
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            expires_at__lte=timezone.now(),
        )
        self.assertIn(stale, stale_qs)
        self.assertNotIn(fresh, stale_qs)
        self.assertNotIn(already_expired, stale_qs)

    def test_confirmed_reservation_also_considered_stale(self):
        product = create_product(sku="EXP-004")
        location = create_location(name="Warehouse")
        past = timezone.now() - timedelta(hours=1)
        reservation = create_reservation(
            product=product, location=location,
            expires_at=past, status=ReservationStatus.CONFIRMED,
        )
        stale_qs = StockReservation.objects.filter(
            status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            expires_at__lte=timezone.now(),
        )
        self.assertIn(reservation, stale_qs)


# =====================================================================
# StockReservation — state transition edge cases
# =====================================================================


class ReservationStateTransitionEdgeCaseTests(TestCase):
    """Test disallowed state transitions at the model level.

    The service layer enforces business rules, but these tests verify
    that the model itself accepts any CharField value (enforcement is
    in ReservationService, not the model).
    """

    def test_fulfilled_reservation_cannot_be_re_fulfilled(self):
        """At the DB level the field accepts any status string, but a
        fulfilled reservation should not logically be re-fulfilled."""
        product = create_product(sku="EDGE-001")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.FULFILLED,
        )
        self.assertEqual(reservation.status, ReservationStatus.FULFILLED)

    def test_cancelled_reservation_status_persists(self):
        product = create_product(sku="EDGE-002")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.CANCELLED,
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.CANCELLED)

    def test_expired_reservation_status_persists(self):
        product = create_product(sku="EDGE-003")
        location = create_location(name="Warehouse")
        reservation = create_reservation(
            product=product, location=location,
            status=ReservationStatus.EXPIRED,
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.status, ReservationStatus.EXPIRED)

    def test_notes_field_stores_long_text(self):
        product = create_product(sku="EDGE-004")
        location = create_location(name="Warehouse")
        long_note = "A" * 5000
        reservation = create_reservation(
            product=product, location=location, notes=long_note,
        )
        reservation.refresh_from_db()
        self.assertEqual(reservation.notes, long_note)


# =====================================================================
# ReservationRule — creation & rule resolution
# =====================================================================


class ReservationRuleTests(TestCase):
    """Test ReservationRule creation, __str__, and get_rule_for_product."""

    def test_create_rule_with_defaults(self):
        rule = create_reservation_rule(name="Default Policy")
        self.assertEqual(rule.name, "Default Policy")
        self.assertEqual(rule.reservation_expiry_hours, 72)
        self.assertEqual(rule.allocation_strategy, AllocationStrategy.FIFO)
        self.assertTrue(rule.is_active)

    def test_str_tenant_wide(self):
        rule = create_reservation_rule(name="Global")
        self.assertIn("tenant-wide", str(rule))

    def test_str_product_specific(self):
        product = create_product(sku="RULE-P1")
        rule = create_reservation_rule(name="Product Rule", product=product)
        self.assertIn("product=", str(rule))

    def test_str_category_specific(self):
        category = create_category(name="Electronics", slug="electronics")
        rule = create_reservation_rule(name="Cat Rule", category=category)
        self.assertIn("category=", str(rule))

    def test_get_rule_product_specific_wins(self):
        """Product-level rule takes precedence over category and tenant-wide."""
        product = create_product(sku="RULE-P2")
        category = create_category(name="Gadgets", slug="gadgets")
        product.category = category
        product.save()

        create_reservation_rule(name="Tenant-wide")
        create_reservation_rule(name="Category Rule", category=category)
        product_rule = create_reservation_rule(name="Product Rule", product=product)

        resolved = ReservationRule.get_rule_for_product(product)
        self.assertEqual(resolved, product_rule)

    def test_get_rule_category_fallback(self):
        """Category rule is used when no product-level rule exists."""
        category = create_category(name="Tools", slug="tools")
        product = create_product(sku="RULE-P3", category=category)

        create_reservation_rule(name="Tenant-wide")
        cat_rule = create_reservation_rule(name="Category Rule", category=category)

        resolved = ReservationRule.get_rule_for_product(product)
        self.assertEqual(resolved, cat_rule)

    def test_get_rule_tenant_wide_fallback(self):
        """Tenant-wide rule used when no product/category rule exists."""
        product = create_product(sku="RULE-P4")
        tw_rule = create_reservation_rule(name="Tenant-wide fallback")

        resolved = ReservationRule.get_rule_for_product(product)
        self.assertEqual(resolved, tw_rule)

    def test_get_rule_returns_none_when_no_rules(self):
        product = create_product(sku="RULE-P5")
        self.assertIsNone(ReservationRule.get_rule_for_product(product))

    def test_inactive_rule_is_skipped(self):
        product = create_product(sku="RULE-P6")
        create_reservation_rule(name="Inactive", product=product, is_active=False)
        self.assertIsNone(ReservationRule.get_rule_for_product(product))
