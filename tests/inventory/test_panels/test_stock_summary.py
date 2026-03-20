"""Tests for the StockSummaryPanel dashboard component."""

from decimal import Decimal

from django.test import TestCase

from inventory.panels.stock_summary import StockSummaryPanel

from ..factories import create_location, create_product, create_stock_record


class StockSummaryPanelTests(TestCase):
    """Test StockSummaryPanel context data computation."""

    def test_panel_with_data(self):
        loc = create_location(name="Warehouse")
        p1 = create_product(sku="SP-001", unit_cost=Decimal("10.00"))
        p2 = create_product(sku="SP-002", unit_cost=Decimal("25.00"))
        create_stock_record(product=p1, location=loc, quantity=100)
        create_stock_record(product=p2, location=loc, quantity=40)

        panel = StockSummaryPanel()
        context = panel.get_context_data()

        self.assertEqual(context["total_products"], 2)
        self.assertEqual(context["total_locations"], 1)
        self.assertEqual(context["total_items"], 140)
        # 100 * 10.00 + 40 * 25.00 = 1000 + 1000 = 2000
        self.assertEqual(context["total_value"], Decimal("2000.00"))

    def test_panel_with_no_data(self):
        panel = StockSummaryPanel()
        context = panel.get_context_data()

        self.assertEqual(context["total_products"], 0)
        self.assertEqual(context["total_locations"], 0)
        self.assertEqual(context["total_items"], 0)
        self.assertEqual(context["total_value"], 0)

    def test_panel_excludes_inactive_products(self):
        create_product(sku="SP-ACTIVE", is_active=True)
        create_product(sku="SP-INACTIVE", is_active=False)

        panel = StockSummaryPanel()
        context = panel.get_context_data()
        self.assertEqual(context["total_products"], 1)

    def test_panel_excludes_inactive_locations(self):
        create_location(name="Active Location", is_active=True)
        create_location(name="Closed Location", is_active=False)

        panel = StockSummaryPanel()
        context = panel.get_context_data()
        self.assertEqual(context["total_locations"], 1)

    def test_panel_attributes(self):
        panel = StockSummaryPanel()
        self.assertEqual(panel.name, "stock_summary")
        self.assertEqual(panel.order, 100)
