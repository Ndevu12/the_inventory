"""Tests for InventoryReportService."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.models import MovementType, ReservationStatus, Warehouse
from inventory.services.stock import StockService
from tenants.context import clear_current_tenant, set_current_tenant
from tests.fixtures.factories import (
    create_category,
    create_location,
    create_product,
    create_reservation,
    create_stock_lot,
    create_stock_record,
    create_tenant,
)

from reports.services.inventory_reports import InventoryReportService


class InventoryReportServiceSetupMixin:
    """Shared setUp that creates products with stock."""

    def setUp(self):
        self.service = InventoryReportService()
        self.stock_service = StockService()
        self.tenant = create_tenant()
        set_current_tenant(self.tenant)
        self.warehouse = create_location(name="Warehouse", tenant=self.tenant)
        self.store = create_location(name="Store", tenant=self.tenant)

        self.product_a = create_product(
            sku="RPT-A", name="Widget A",
            unit_cost=Decimal("10.00"), reorder_point=20, tenant=self.tenant,
        )
        self.product_b = create_product(
            sku="RPT-B", name="Widget B",
            unit_cost=Decimal("25.00"), reorder_point=10, tenant=self.tenant,
        )


# =====================================================================
# Stock Valuation
# =====================================================================


class StockValuationTests(InventoryReportServiceSetupMixin, TestCase):
    """Test stock valuation calculations."""

    def test_latest_cost_valuation(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        valuations = self.service.get_stock_valuation(method="latest_cost")

        self.assertEqual(len(valuations), 1)
        v = valuations[0]
        self.assertEqual(v.product, self.product_a)
        self.assertEqual(v.total_quantity, 100)
        self.assertEqual(v.unit_cost, Decimal("10.00"))
        self.assertEqual(v.total_value, Decimal("1000.00"))

    def test_weighted_average_valuation(self):
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            unit_cost=Decimal("10.00"),
        )
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            unit_cost=Decimal("20.00"),
        )

        valuations = self.service.get_stock_valuation(method="weighted_average")
        self.assertEqual(len(valuations), 1)
        v = valuations[0]
        self.assertEqual(v.total_quantity, 200)
        self.assertEqual(v.unit_cost, Decimal("15.00"))
        self.assertEqual(v.total_value, Decimal("3000.00"))

    def test_valuation_excludes_zero_stock(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=0,
        )
        valuations = self.service.get_stock_valuation(method="latest_cost")
        self.assertEqual(len(valuations), 0)

    def test_valuation_excludes_inactive_products(self):
        inactive = create_product(
            sku="RPT-INACTIVE", is_active=False,
            unit_cost=Decimal("5.00"), tenant=self.tenant,
        )
        create_stock_record(
            product=inactive, location=self.warehouse, quantity=50,
        )
        valuations = self.service.get_stock_valuation(method="latest_cost")
        skus = [v.product.sku for v in valuations]
        self.assertNotIn("RPT-INACTIVE", skus)

    def test_valuation_summary(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product_b, location=self.warehouse, quantity=50,
        )
        summary = self.service.get_valuation_summary(method="latest_cost")

        self.assertEqual(summary["total_products"], 2)
        self.assertEqual(summary["total_quantity"], 150)
        self.assertEqual(
            summary["total_value"],
            Decimal("100") * Decimal("10.00") + Decimal("50") * Decimal("25.00"),
        )

    def test_unknown_method_raises_error(self):
        with self.assertRaises(ValueError):
            self.service.get_stock_valuation(method="fifo")

    def test_valuation_scoped_to_facility_warehouse(self):
        dc_a = Warehouse.objects.create(tenant=self.tenant, name="DC A")
        dc_b = Warehouse.objects.create(tenant=self.tenant, name="DC B")
        loc_a = create_location(
            name="Bin A", tenant=self.tenant, warehouse=dc_a,
        )
        loc_b = create_location(
            name="Bin B", tenant=self.tenant, warehouse=dc_b,
        )
        create_stock_record(
            product=self.product_a, location=loc_a, quantity=100,
        )
        create_stock_record(
            product=self.product_a, location=loc_b, quantity=50,
        )
        vals = self.service.get_stock_valuation(
            method="latest_cost",
            tenant=self.tenant,
            warehouse_id=dc_a.pk,
        )
        self.assertEqual(len(vals), 1)
        self.assertEqual(vals[0].total_quantity, 100)

    def test_weighted_average_fallback_to_product_cost(self):
        """If no receive movements, fall back to product.unit_cost."""
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=50,
        )
        valuations = self.service.get_stock_valuation(method="weighted_average")
        self.assertEqual(len(valuations), 1)
        self.assertEqual(valuations[0].unit_cost, Decimal("10.00"))


# =====================================================================
# Stock Level Reports
# =====================================================================


class LowStockReportTests(InventoryReportServiceSetupMixin, TestCase):
    """Test low-stock product reporting."""

    def test_returns_low_stock_products(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=5,
        )
        products = self.service.get_low_stock_products()
        skus = [p.sku for p in products]
        self.assertIn("RPT-A", skus)

    def test_excludes_adequately_stocked(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        products = self.service.get_low_stock_products()
        skus = [p.sku for p in products]
        self.assertNotIn("RPT-A", skus)

    def test_excludes_zero_reorder_point(self):
        no_alert = create_product(
            sku="RPT-NOALERT", reorder_point=0, tenant=self.tenant,
        )
        create_stock_record(
            product=no_alert, location=self.warehouse, quantity=0,
        )
        products = self.service.get_low_stock_products()
        skus = [p.sku for p in products]
        self.assertNotIn("RPT-NOALERT", skus)


class OverstockReportTests(InventoryReportServiceSetupMixin, TestCase):
    """Test overstock product reporting."""

    def test_returns_overstocked_products(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        products = self.service.get_overstock_products(threshold_multiplier=3)
        skus = [p.sku for p in products]
        self.assertIn("RPT-A", skus)

    def test_excludes_normal_stock(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=30,
        )
        products = self.service.get_overstock_products(threshold_multiplier=3)
        skus = [p.sku for p in products]
        self.assertNotIn("RPT-A", skus)

    def test_custom_threshold(self):
        create_stock_record(
            product=self.product_b, location=self.warehouse, quantity=25,
        )
        products_2x = self.service.get_overstock_products(threshold_multiplier=2)
        skus_2x = [p.sku for p in products_2x]
        self.assertIn("RPT-B", skus_2x)

        products_5x = self.service.get_overstock_products(threshold_multiplier=5)
        skus_5x = [p.sku for p in products_5x]
        self.assertNotIn("RPT-B", skus_5x)


# =====================================================================
# Movement History
# =====================================================================


class MovementHistoryTests(InventoryReportServiceSetupMixin, TestCase):
    """Test movement history reporting."""

    def setUp(self):
        super().setUp()
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
        )

    def test_returns_all_movements(self):
        movements = self.service.get_movement_history()
        self.assertEqual(movements.count(), 2)

    def test_filter_by_movement_type(self):
        movements = self.service.get_movement_history(
            movement_type=MovementType.RECEIVE,
        )
        self.assertEqual(movements.count(), 1)
        self.assertEqual(
            movements.first().movement_type, MovementType.RECEIVE,
        )

    def test_filter_by_product(self):
        self.stock_service.process_movement(
            product=self.product_b,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )
        movements = self.service.get_movement_history(
            product=self.product_a,
        )
        self.assertEqual(movements.count(), 2)

    def test_filter_by_location(self):
        movements = self.service.get_movement_history(
            location=self.warehouse,
        )
        self.assertEqual(movements.count(), 2)

    def test_filter_by_date_range(self):
        tomorrow = date.today() + timedelta(days=1)
        movements = self.service.get_movement_history(
            date_from=tomorrow,
        )
        self.assertEqual(movements.count(), 0)

    def test_movement_summary(self):
        summary = self.service.get_movement_summary()
        self.assertEqual(summary["receive"]["count"], 1)
        self.assertEqual(summary["receive"]["total_quantity"], 100)
        self.assertEqual(summary["issue"]["count"], 1)
        self.assertEqual(summary["issue"]["total_quantity"], 20)


# =====================================================================
# Reservation Summary
# =====================================================================


class ReservationSummaryTests(InventoryReportServiceSetupMixin, TestCase):
    """Test reservation summary reporting."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product_b, location=self.store, quantity=50,
        )

    def test_empty_when_no_reservations(self):
        summary = self.service.get_reservation_summary()
        self.assertEqual(summary["total_active_reservations"], 0)
        self.assertEqual(summary["total_reserved_quantity"], 0)
        self.assertEqual(summary["by_status"], {})

    def test_counts_by_status(self):
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=10, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=20, status=ReservationStatus.CONFIRMED,
        )
        create_reservation(
            product=self.product_b, location=self.store,
            quantity=5, status=ReservationStatus.CANCELLED,
        )

        summary = self.service.get_reservation_summary()
        self.assertEqual(summary["by_status"]["pending"]["count"], 1)
        self.assertEqual(summary["by_status"]["pending"]["total_quantity"], 10)
        self.assertEqual(summary["by_status"]["confirmed"]["count"], 1)
        self.assertEqual(summary["by_status"]["confirmed"]["total_quantity"], 20)
        self.assertEqual(summary["by_status"]["cancelled"]["count"], 1)

    def test_active_totals_exclude_non_active_statuses(self):
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=10, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=15, status=ReservationStatus.CONFIRMED,
        )
        create_reservation(
            product=self.product_b, location=self.store,
            quantity=5, status=ReservationStatus.FULFILLED,
        )
        create_reservation(
            product=self.product_b, location=self.store,
            quantity=8, status=ReservationStatus.EXPIRED,
        )

        summary = self.service.get_reservation_summary()
        self.assertEqual(summary["total_active_reservations"], 2)
        self.assertEqual(summary["total_reserved_quantity"], 25)


# =====================================================================
# Availability Report
# =====================================================================


class AvailabilityReportTests(InventoryReportServiceSetupMixin, TestCase):
    """Test per-product availability reporting."""

    def setUp(self):
        super().setUp()
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product_b, location=self.store, quantity=50,
        )

    def test_availability_with_no_reservations(self):
        results = self.service.get_availability_report()
        self.assertEqual(len(results), 2)
        item_a = next(r for r in results if r["sku"] == "RPT-A")
        self.assertEqual(item_a["total_quantity"], 100)
        self.assertEqual(item_a["reserved_quantity"], 0)
        self.assertEqual(item_a["available_quantity"], 100)

    def test_availability_with_active_reservations(self):
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=30, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=10, status=ReservationStatus.CONFIRMED,
        )

        results = self.service.get_availability_report()
        item_a = next(r for r in results if r["sku"] == "RPT-A")
        self.assertEqual(item_a["reserved_quantity"], 40)
        self.assertEqual(item_a["available_quantity"], 60)

    def test_availability_ignores_non_active_reservations(self):
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=30, status=ReservationStatus.FULFILLED,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=10, status=ReservationStatus.CANCELLED,
        )

        results = self.service.get_availability_report()
        item_a = next(r for r in results if r["sku"] == "RPT-A")
        self.assertEqual(item_a["reserved_quantity"], 0)
        self.assertEqual(item_a["available_quantity"], 100)

    def test_filter_by_category(self):
        cat = create_category(
            name="Electronics", slug="electronics", tenant=self.tenant,
        )
        self.product_a.category = cat
        self.product_a.save()

        results = self.service.get_availability_report(category_id=cat.pk)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sku"], "RPT-A")

    def test_filter_by_product(self):
        results = self.service.get_availability_report(
            product_id=self.product_b.pk,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["sku"], "RPT-B")

    def test_reserved_value_calculation(self):
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=20, status=ReservationStatus.PENDING,
        )
        results = self.service.get_availability_report()
        item_a = next(r for r in results if r["sku"] == "RPT-A")
        self.assertEqual(
            item_a["reserved_value"],
            20 * Decimal("10.00"),
        )

    def test_excludes_inactive_products(self):
        inactive = create_product(
            sku="RPT-INACTIVE", is_active=False,
            unit_cost=Decimal("5.00"), tenant=self.tenant,
        )
        create_stock_record(
            product=inactive, location=self.warehouse, quantity=50,
        )
        results = self.service.get_availability_report()
        skus = [r["sku"] for r in results]
        self.assertNotIn("RPT-INACTIVE", skus)

    def test_products_sorted_by_sku(self):
        results = self.service.get_availability_report()
        skus = [r["sku"] for r in results]
        self.assertEqual(skus, sorted(skus))


# =====================================================================
# Reserved Stock Value KPI
# =====================================================================


class ReservedStockValueTests(InventoryReportServiceSetupMixin, TestCase):
    """Test the reserved stock value dashboard KPI."""

    def test_zero_when_no_reservations(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        value = self.service.get_reserved_stock_value()
        self.assertEqual(value, Decimal("0.00"))

    def test_correct_value_with_reservations(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        create_stock_record(
            product=self.product_b, location=self.store, quantity=50,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=10, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product_b, location=self.store,
            quantity=5, status=ReservationStatus.CONFIRMED,
        )

        value = self.service.get_reserved_stock_value()
        expected = (10 * Decimal("10.00")) + (5 * Decimal("25.00"))
        self.assertEqual(value, expected)

    def test_ignores_non_active_reservations(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=100,
        )
        create_reservation(
            product=self.product_a, location=self.warehouse,
            quantity=50, status=ReservationStatus.FULFILLED,
        )
        value = self.service.get_reserved_stock_value()
        self.assertEqual(value, Decimal("0.00"))


# =====================================================================
# Expiring Lots
# =====================================================================


class ExpiringLotsTests(InventoryReportServiceSetupMixin, TestCase):
    """Test get_expiring_lots service method."""

    def test_returns_lots_within_window(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-10",
            expiry_date=date.today() + timedelta(days=10),
        )
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-25",
            expiry_date=date.today() + timedelta(days=25),
        )
        lots = self.service.get_expiring_lots(days_ahead=30)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("EXP-10", lot_numbers)
        self.assertIn("EXP-25", lot_numbers)

    def test_excludes_lots_beyond_window(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-FAR",
            expiry_date=date.today() + timedelta(days=60),
        )
        lots = self.service.get_expiring_lots(days_ahead=30)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("EXP-FAR", lot_numbers)

    def test_excludes_already_expired(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-PAST",
            expiry_date=date.today() - timedelta(days=1),
        )
        lots = self.service.get_expiring_lots(days_ahead=30)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("EXP-PAST", lot_numbers)

    def test_excludes_depleted_lots(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-DEPLETED",
            expiry_date=date.today() + timedelta(days=10),
            quantity_remaining=0,
        )
        lots = self.service.get_expiring_lots(days_ahead=30)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("EXP-DEPLETED", lot_numbers)

    def test_excludes_lots_without_expiry(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="NO-EXPIRY",
            expiry_date=None,
        )
        lots = self.service.get_expiring_lots(days_ahead=30)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("NO-EXPIRY", lot_numbers)

    def test_filter_by_product(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-A",
            expiry_date=date.today() + timedelta(days=10),
        )
        create_stock_lot(
            product=self.product_b,
            lot_number="EXP-B",
            expiry_date=date.today() + timedelta(days=10),
        )
        lots = self.service.get_expiring_lots(
            days_ahead=30, product=self.product_a,
        )
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("EXP-A", lot_numbers)
        self.assertNotIn("EXP-B", lot_numbers)

    def test_filter_by_location(self):
        create_stock_record(
            product=self.product_a, location=self.warehouse, quantity=50,
        )
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-WH",
            expiry_date=date.today() + timedelta(days=10),
        )
        lots = self.service.get_expiring_lots(
            days_ahead=30, location=self.warehouse,
        )
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("EXP-WH", lot_numbers)

    def test_ordered_by_expiry_date(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-LATER",
            expiry_date=date.today() + timedelta(days=20),
        )
        create_stock_lot(
            product=self.product_a,
            lot_number="EXP-SOONER",
            expiry_date=date.today() + timedelta(days=5),
        )
        lots = list(self.service.get_expiring_lots(days_ahead=30))
        self.assertEqual(lots[0].lot_number, "EXP-SOONER")
        self.assertEqual(lots[1].lot_number, "EXP-LATER")


# =====================================================================
# Expired Lots
# =====================================================================


class ExpiredLotsTests(InventoryReportServiceSetupMixin, TestCase):
    """Test get_expired_lots service method."""

    def test_returns_expired_lots(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="PAST-1",
            expiry_date=date.today() - timedelta(days=5),
        )
        lots = self.service.get_expired_lots()
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("PAST-1", lot_numbers)

    def test_excludes_future_expiry(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="FUTURE-1",
            expiry_date=date.today() + timedelta(days=10),
        )
        lots = self.service.get_expired_lots()
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("FUTURE-1", lot_numbers)

    def test_excludes_depleted_by_default(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="PAST-DEPLETED",
            expiry_date=date.today() - timedelta(days=5),
            quantity_remaining=0,
        )
        lots = self.service.get_expired_lots()
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertNotIn("PAST-DEPLETED", lot_numbers)

    def test_includes_depleted_when_requested(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="PAST-DEPLETED",
            expiry_date=date.today() - timedelta(days=5),
            quantity_remaining=0,
        )
        lots = self.service.get_expired_lots(include_depleted=True)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("PAST-DEPLETED", lot_numbers)

    def test_filter_by_product(self):
        create_stock_lot(
            product=self.product_a,
            lot_number="PAST-A",
            expiry_date=date.today() - timedelta(days=3),
        )
        create_stock_lot(
            product=self.product_b,
            lot_number="PAST-B",
            expiry_date=date.today() - timedelta(days=3),
        )
        lots = self.service.get_expired_lots(product=self.product_a)
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("PAST-A", lot_numbers)
        self.assertNotIn("PAST-B", lot_numbers)

    def test_includes_today_as_expired(self):
        """Lots expiring today (expiry_date <= today) are considered expired."""
        create_stock_lot(
            product=self.product_a,
            lot_number="TODAY",
            expiry_date=date.today(),
        )
        lots = self.service.get_expired_lots()
        lot_numbers = [lot.lot_number for lot in lots]
        self.assertIn("TODAY", lot_numbers)


# =====================================================================
# Lot History
# =====================================================================


class LotHistoryTests(InventoryReportServiceSetupMixin, TestCase):
    """Test get_lot_history service method."""

    def test_returns_movements_for_lot(self):
        from inventory.models import StockMovementLot

        lot = create_stock_lot(
            product=self.product_a, lot_number="HIST-001",
        )
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        movement = self.product_a.stock_movements.first()
        StockMovementLot.objects.create(
            stock_movement=movement, stock_lot=lot, quantity=100,
        )

        history = self.service.get_lot_history(
            product=self.product_a, lot_number="HIST-001",
        )
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().pk, movement.pk)

    def test_returns_empty_for_unknown_lot(self):
        history = self.service.get_lot_history(
            product=self.product_a, lot_number="NONEXISTENT",
        )
        self.assertEqual(history.count(), 0)

    def test_multiple_movements_for_lot(self):
        from inventory.models import StockMovementLot

        lot = create_stock_lot(
            product=self.product_a, lot_number="HIST-002",
        )

        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        recv = self.product_a.stock_movements.order_by("created_at").last()
        StockMovementLot.objects.create(
            stock_movement=recv, stock_lot=lot, quantity=100,
        )

        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.ISSUE,
            quantity=30,
            from_location=self.warehouse,
        )
        issue = self.product_a.stock_movements.order_by("-created_at").first()
        StockMovementLot.objects.create(
            stock_movement=issue, stock_lot=lot, quantity=30,
        )

        history = self.service.get_lot_history(
            product=self.product_a, lot_number="HIST-002",
        )
        self.assertEqual(history.count(), 2)

    def test_excludes_unrelated_movements(self):
        from inventory.models import StockMovementLot

        lot = create_stock_lot(
            product=self.product_a, lot_number="HIST-003",
        )
        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
        )
        movement = self.product_a.stock_movements.first()
        StockMovementLot.objects.create(
            stock_movement=movement, stock_lot=lot, quantity=100,
        )

        self.stock_service.process_movement(
            product=self.product_a,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
        )

        history = self.service.get_lot_history(
            product=self.product_a, lot_number="HIST-003",
        )
        self.assertEqual(history.count(), 1)


# =====================================================================
# Tenant Security
# =====================================================================


class InventoryReportTenantSecurityTests(TestCase):
    """Test that report methods enforce tenant isolation."""

    def setUp(self):
        self.service = InventoryReportService()
        self.stock_service = StockService()
        self.tenant1 = create_tenant(name="Tenant 1", slug="tenant-1")
        self.tenant2 = create_tenant(name="Tenant 2", slug="tenant-2")

        set_current_tenant(self.tenant1)
        self.loc1 = create_location(name="WH1", tenant=self.tenant1)
        self.prod1 = create_product(
            sku="T1-P1", name="Tenant1 Product",
            unit_cost=Decimal("10.00"), reorder_point=10, tenant=self.tenant1,
        )
        create_stock_record(self.prod1, self.loc1, quantity=50)

        set_current_tenant(self.tenant2)
        self.loc2 = create_location(name="WH2", tenant=self.tenant2)
        self.prod2 = create_product(
            sku="T2-P1", name="Tenant2 Product",
            unit_cost=Decimal("20.00"), reorder_point=5, tenant=self.tenant2,
        )
        create_stock_record(self.prod2, self.loc2, quantity=100)

    def test_no_tenant_raises_value_error(self):
        """Raises ValueError when no tenant in context and none provided."""
        clear_current_tenant()
        with self.assertRaises(ValueError) as ctx:
            self.service.get_stock_valuation(method="latest_cost")
        self.assertIn("No tenant", str(ctx.exception))

    def test_stock_valuation_returns_only_current_tenant_data(self):
        """get_stock_valuation returns only products for the specified tenant."""
        set_current_tenant(self.tenant1)
        valuations = self.service.get_stock_valuation(
            method="latest_cost", tenant=self.tenant1,
        )
        skus = [v.product.sku for v in valuations]
        self.assertIn("T1-P1", skus)
        self.assertNotIn("T2-P1", skus)

        valuations = self.service.get_stock_valuation(
            method="latest_cost", tenant=self.tenant2,
        )
        skus = [v.product.sku for v in valuations]
        self.assertIn("T2-P1", skus)
        self.assertNotIn("T1-P1", skus)

    def test_movement_history_filters_by_tenant(self):
        """get_movement_history returns only movements for the tenant."""
        set_current_tenant(self.tenant1)
        self.stock_service.process_movement(
            product=self.prod1,
            movement_type=MovementType.RECEIVE,
            quantity=25,
            to_location=self.loc1,
        )
        set_current_tenant(self.tenant2)
        self.stock_service.process_movement(
            product=self.prod2,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.loc2,
        )

        set_current_tenant(self.tenant1)
        movements = self.service.get_movement_history(tenant=self.tenant1)
        self.assertEqual(movements.count(), 1)
        self.assertEqual(movements.first().product.sku, "T1-P1")

    def test_product_traceability_returns_none_for_other_tenant_sku(self):
        """get_product_traceability returns None for SKU belonging to another tenant."""
        set_current_tenant(self.tenant1)
        create_stock_lot(self.prod1, lot_number="LOT-1")
        result = self.service.get_product_traceability(
            sku="T2-P1", lot_number="LOT-1", tenant=self.tenant1,
        )
        self.assertIsNone(result)
