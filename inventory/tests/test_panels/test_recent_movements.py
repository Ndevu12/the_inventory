"""Tests for the RecentMovementsPanel dashboard component."""

from django.test import TestCase

from inventory.models import MovementType
from inventory.panels.recent_movements import RecentMovementsPanel
from inventory.services.stock import StockService

from ..factories import create_location, create_product


class RecentMovementsPanelTests(TestCase):
    """Test RecentMovementsPanel context data computation."""

    def setUp(self):
        self.service = StockService()
        self.product = create_product(sku="RMP-001")
        self.location = create_location(name="Warehouse")

    def test_panel_shows_recent_movements(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.location,
        )

        panel = RecentMovementsPanel()
        context = panel.get_context_data()
        movements = list(context["recent_movements"])

        self.assertEqual(len(movements), 1)
        self.assertEqual(movements[0].product.sku, "RMP-001")

    def test_panel_orders_most_recent_first(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.location,
            reference="first",
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=20,
            to_location=self.location,
            reference="second",
        )

        panel = RecentMovementsPanel()
        context = panel.get_context_data()
        movements = list(context["recent_movements"])

        self.assertEqual(movements[0].reference, "second")
        self.assertEqual(movements[1].reference, "first")

    def test_panel_limits_to_10(self):
        for i in range(15):
            self.service.process_movement(
                product=self.product,
                movement_type=MovementType.RECEIVE,
                quantity=1,
                to_location=self.location,
            )

        panel = RecentMovementsPanel()
        context = panel.get_context_data()
        self.assertEqual(len(list(context["recent_movements"])), 10)

    def test_panel_with_no_movements(self):
        panel = RecentMovementsPanel()
        context = panel.get_context_data()
        self.assertEqual(len(list(context["recent_movements"])), 0)

    def test_panel_attributes(self):
        panel = RecentMovementsPanel()
        self.assertEqual(panel.name, "recent_movements")
        self.assertEqual(panel.order, 120)
