"""Tests for InventoryReportService."""

from datetime import date, timedelta
from decimal import Decimal

from django.test import TestCase

from inventory.models import MovementType
from inventory.services.stock import StockService
from inventory.tests.factories import create_location, create_product, create_stock_record

from reports.services.inventory_reports import InventoryReportService


class InventoryReportServiceSetupMixin:
    """Shared setUp that creates products with stock."""

    def setUp(self):
        self.service = InventoryReportService()
        self.stock_service = StockService()
        self.warehouse = create_location(name="Warehouse")
        self.store = create_location(name="Store")

        self.product_a = create_product(
            sku="RPT-A", name="Widget A",
            unit_cost=Decimal("10.00"), reorder_point=20,
        )
        self.product_b = create_product(
            sku="RPT-B", name="Widget B",
            unit_cost=Decimal("25.00"), reorder_point=10,
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
            unit_cost=Decimal("5.00"),
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
        no_alert = create_product(sku="RPT-NOALERT", reorder_point=0)
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
