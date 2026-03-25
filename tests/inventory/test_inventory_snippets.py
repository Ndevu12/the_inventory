"""Warehouse and stock location snippet registration for Wagtail admin."""

from django.test import TestCase
from wagtail.snippets.models import get_snippet_models

from inventory.models import StockLocation, Warehouse


class InventorySitesSnippetRegistrationTests(TestCase):
    def test_warehouse_and_stocklocation_are_snippets(self):
        registered = get_snippet_models()
        for model in (Warehouse, StockLocation):
            with self.subTest(model=model.__name__):
                self.assertIn(model, registered)
                self.assertIsNotNone(getattr(model, "snippet_viewset", None))
