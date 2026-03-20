"""Tests for the LowStockPanel dashboard component."""

from django.test import TestCase

from inventory.panels.low_stock import LowStockPanel

from ..factories import create_location, create_product, create_stock_record


class LowStockPanelTests(TestCase):
    """Test LowStockPanel context data computation."""

    def test_panel_shows_low_stock_items(self):
        loc = create_location(name="Warehouse")
        product = create_product(sku="LSP-001", reorder_point=20)
        create_stock_record(product=product, location=loc, quantity=5)

        panel = LowStockPanel()
        context = panel.get_context_data()
        records = list(context["low_stock_records"])

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].product.sku, "LSP-001")

    def test_panel_orders_by_deficit_descending(self):
        loc = create_location(name="Warehouse")

        # Deficit 17 (reorder 20, quantity 3)
        p1 = create_product(sku="LSP-HIGH", reorder_point=20)
        create_stock_record(product=p1, location=loc, quantity=3)

        # Deficit 2 (reorder 10, quantity 8)
        p2 = create_product(sku="LSP-MILD", reorder_point=10)
        create_stock_record(product=p2, location=loc, quantity=8)

        panel = LowStockPanel()
        context = panel.get_context_data()
        records = list(context["low_stock_records"])

        self.assertEqual(records[0].product.sku, "LSP-HIGH")
        self.assertEqual(records[1].product.sku, "LSP-MILD")

    def test_panel_limits_to_10(self):
        loc = create_location(name="Warehouse")
        for i in range(15):
            product = create_product(
                sku=f"LSP-{i:03d}", reorder_point=100,
            )
            create_stock_record(product=product, location=loc, quantity=1)

        panel = LowStockPanel()
        context = panel.get_context_data()
        self.assertEqual(len(list(context["low_stock_records"])), 10)

    def test_panel_with_no_low_stock(self):
        panel = LowStockPanel()
        context = panel.get_context_data()
        self.assertEqual(len(list(context["low_stock_records"])), 0)

    def test_panel_excludes_zero_reorder_point(self):
        """Products with reorder_point=0 should not appear."""
        loc = create_location(name="Warehouse")
        product = create_product(sku="LSP-ZERO", reorder_point=0)
        create_stock_record(product=product, location=loc, quantity=0)

        panel = LowStockPanel()
        context = panel.get_context_data()
        self.assertEqual(len(list(context["low_stock_records"])), 0)

    def test_panel_attributes(self):
        panel = LowStockPanel()
        self.assertEqual(panel.name, "low_stock")
        self.assertEqual(panel.order, 110)
