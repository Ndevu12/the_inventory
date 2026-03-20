"""Tests for SalesService auto-reservation on order confirmation (T-15).

Covers:
- Auto-reservation creates StockReservation when rule is active
- No reservation when rule is inactive or missing
- Lot auto-assignment during auto-reservation
- Skipped when no default_location is provided
"""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.models import ReservationStatus, StockReservation
from inventory.models.reservation import AllocationStrategy
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_reservation_rule,
    create_stock_lot,
    create_stock_record,
    create_user,
)
from sales.services.sales import SalesService
from tests.fixtures.factories import create_customer, create_sales_order, create_sales_order_line


class AutoReservationSetupMixin:
    """Shared setup for auto-reservation tests."""

    def setUp(self):
        self.service = SalesService()
        self.warehouse = create_location(name="Auto-Res Warehouse")
        self.product = create_product(
            sku="AUTO-001",
            unit_cost=Decimal("10.00"),
            tracking_mode="optional",
        )
        create_stock_record(
            product=self.product,
            location=self.warehouse,
            quantity=500,
        )
        self.customer = create_customer(code="AR-CUST-001")
        self.user = create_user(username="confirmer")


# =====================================================================
# Auto-reservation on confirm
# =====================================================================


class AutoReservationOnConfirmTests(AutoReservationSetupMixin, TestCase):
    """Test that confirm_order auto-creates reservations."""

    def test_auto_reserve_creates_reservation(self):
        create_reservation_rule(
            name="Auto Rule",
            product=self.product,
            auto_reserve_on_order=True,
        )
        so = create_sales_order(
            order_number="SO-AR-001",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=50,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        reservations = StockReservation.objects.filter(
            sales_order=so, product=self.product,
        )
        self.assertEqual(reservations.count(), 1)
        res = reservations.first()
        self.assertEqual(res.quantity, 50)
        self.assertEqual(res.location, self.warehouse)
        self.assertEqual(res.status, ReservationStatus.PENDING)

    def test_no_rule_no_reservation(self):
        so = create_sales_order(
            order_number="SO-AR-002",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=30,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        self.assertEqual(StockReservation.objects.count(), 0)

    def test_inactive_rule_no_reservation(self):
        create_reservation_rule(
            name="Inactive Rule",
            product=self.product,
            auto_reserve_on_order=True,
            is_active=False,
        )
        so = create_sales_order(
            order_number="SO-AR-003",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=20,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        self.assertEqual(StockReservation.objects.count(), 0)

    def test_rule_without_auto_flag_no_reservation(self):
        create_reservation_rule(
            name="Manual Rule",
            product=self.product,
            auto_reserve_on_order=False,
        )
        so = create_sales_order(
            order_number="SO-AR-004",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=20,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        self.assertEqual(StockReservation.objects.count(), 0)


# =====================================================================
# Auto-reservation with lot assignment
# =====================================================================


class AutoReservationWithLotTests(AutoReservationSetupMixin, TestCase):
    """Test that auto-reservation assigns lots via allocation strategy."""

    def test_auto_reserve_assigns_fifo_lot(self):
        lot_old = create_stock_lot(
            product=self.product,
            lot_number="AUTO-LOT-OLD",
            quantity_received=200,
            quantity_remaining=200,
            received_date=date.today() - timedelta(days=30),
        )
        create_stock_lot(
            product=self.product,
            lot_number="AUTO-LOT-NEW",
            quantity_received=200,
            quantity_remaining=200,
            received_date=date.today(),
        )
        create_reservation_rule(
            name="FIFO Auto Rule",
            product=self.product,
            auto_reserve_on_order=True,
            allocation_strategy=AllocationStrategy.FIFO,
        )
        so = create_sales_order(
            order_number="SO-ARLOT-001",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=80,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        res = StockReservation.objects.get(sales_order=so)
        self.assertEqual(res.stock_lot, lot_old)

    def test_auto_reserve_assigns_lifo_lot(self):
        create_stock_lot(
            product=self.product,
            lot_number="AUTO-LIFO-OLD",
            quantity_received=200,
            quantity_remaining=200,
            received_date=date.today() - timedelta(days=30),
        )
        lot_new = create_stock_lot(
            product=self.product,
            lot_number="AUTO-LIFO-NEW",
            quantity_received=200,
            quantity_remaining=200,
            received_date=date.today(),
        )
        create_reservation_rule(
            name="LIFO Auto Rule",
            product=self.product,
            auto_reserve_on_order=True,
            allocation_strategy=AllocationStrategy.LIFO,
        )
        so = create_sales_order(
            order_number="SO-ARLOT-002",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=80,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        res = StockReservation.objects.get(sales_order=so)
        self.assertEqual(res.stock_lot, lot_new)


# =====================================================================
# Skipped when no default_location
# =====================================================================


class AutoReservationNoLocationTests(AutoReservationSetupMixin, TestCase):
    """Reservation is skipped (not errored) when no default_location."""

    def test_no_location_skips_reservation(self):
        create_reservation_rule(
            name="Auto Rule",
            product=self.product,
            auto_reserve_on_order=True,
        )
        so = create_sales_order(
            order_number="SO-NOLOC-001",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so,
            product=self.product,
            quantity=50,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
        )

        self.assertEqual(StockReservation.objects.count(), 0)


# =====================================================================
# Multiple line items
# =====================================================================


class AutoReservationMultiLineTests(AutoReservationSetupMixin, TestCase):
    """Test auto-reservation across multiple order lines."""

    def test_multiple_lines_creates_multiple_reservations(self):
        product_b = create_product(
            sku="AUTO-002",
            unit_cost=Decimal("5.00"),
        )
        create_stock_record(
            product=product_b, location=self.warehouse, quantity=300,
        )
        create_reservation_rule(
            name="Rule A",
            product=self.product,
            auto_reserve_on_order=True,
        )
        create_reservation_rule(
            name="Rule B",
            product=product_b,
            auto_reserve_on_order=True,
        )

        so = create_sales_order(
            order_number="SO-ML-001",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so, product=self.product, quantity=25,
        )
        create_sales_order_line(
            sales_order=so, product=product_b, quantity=40,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        self.assertEqual(
            StockReservation.objects.filter(sales_order=so).count(), 2,
        )
        res_a = StockReservation.objects.get(
            sales_order=so, product=self.product,
        )
        res_b = StockReservation.objects.get(
            sales_order=so, product=product_b,
        )
        self.assertEqual(res_a.quantity, 25)
        self.assertEqual(res_b.quantity, 40)

    def test_partial_auto_reserve_only_matching_lines(self):
        """Only lines whose product has an active auto-reserve rule get reserved."""
        product_no_rule = create_product(
            sku="AUTO-NORULE",
            unit_cost=Decimal("5.00"),
        )
        create_stock_record(
            product=product_no_rule, location=self.warehouse, quantity=300,
        )
        create_reservation_rule(
            name="Auto Only",
            product=self.product,
            auto_reserve_on_order=True,
        )

        so = create_sales_order(
            order_number="SO-PARTIAL-001",
            customer=self.customer,
        )
        create_sales_order_line(
            sales_order=so, product=self.product, quantity=15,
        )
        create_sales_order_line(
            sales_order=so, product=product_no_rule, quantity=20,
        )

        self.service.confirm_order(
            sales_order=so,
            confirmed_by=self.user,
            default_location=self.warehouse,
        )

        self.assertEqual(
            StockReservation.objects.filter(sales_order=so).count(), 1,
        )
        res = StockReservation.objects.get(sales_order=so)
        self.assertEqual(res.product, self.product)
