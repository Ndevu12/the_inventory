"""Tests for inventory admin views."""

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils import WagtailTestUtils

from inventory.models import Category, Product, StockLocation

from .factories import (
    create_category,
    create_location,
    create_product,
    create_stock_record,
)


class LowStockAlertViewTests(WagtailTestUtils, TestCase):
    """Test the LowStockAlertView admin view."""

    def setUp(self):
        self.user = self.login()
        self.url = reverse("inventory_low_stock")
        self.location = create_location(name="Warehouse")

    def test_view_accessible_by_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        # Wagtail admin redirects to login
        self.assertEqual(response.status_code, 302)

    def test_view_shows_low_stock_products(self):
        low = create_product(sku="VIEW-LOW", name="Low Item", reorder_point=10)
        create_stock_record(product=low, location=self.location, quantity=2)

        ok = create_product(sku="VIEW-OK", name="OK Item", reorder_point=5)
        create_stock_record(product=ok, location=self.location, quantity=50)

        response = self.client.get(self.url)
        self.assertContains(response, "VIEW-LOW")
        self.assertNotContains(response, "VIEW-OK")

    def test_view_with_no_low_stock(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_count"], 0)

    def test_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "inventory/low_stock_alerts.html")

    def test_filter_by_category(self):
        cat = create_category(name="Electronics", slug="electronics")
        p1 = create_product(sku="FC-001", category=cat, reorder_point=10)
        create_stock_record(product=p1, location=self.location, quantity=2)

        p2 = create_product(sku="FC-002", reorder_point=10)
        create_stock_record(product=p2, location=self.location, quantity=2)

        response = self.client.get(self.url, {"category": cat.pk})
        self.assertContains(response, "FC-001")
        self.assertNotContains(response, "FC-002")

    def test_pagination_context(self):
        """View has paginate_by=25, ensure context contains paginator."""
        response = self.client.get(self.url)
        self.assertIn("paginator", response.context)


class InventorySearchViewTests(WagtailTestUtils, TestCase):
    """Test the InventorySearchView admin view.

    Search result tests use mocked backends to isolate our view logic
    from the Wagtail search backend implementation (which varies by
    database engine and requires index rebuilds).
    """

    def setUp(self):
        self.user = self.login()
        self.url = reverse("inventory_search")

    def test_view_accessible_by_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_view_uses_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "inventory/search.html")

    def test_empty_query_returns_empty_results(self):
        response = self.client.get(self.url)
        self.assertEqual(response.context["search_query"], "")
        self.assertEqual(response.context["product_results"].count(), 0)
        self.assertEqual(response.context["category_results"].count(), 0)
        self.assertEqual(response.context["location_results"].count(), 0)

    def test_search_with_query_passes_context(self):
        """Verify the query string is passed through to the template context."""
        response = self.client.get(self.url, {"q": "widget"})
        self.assertEqual(response.context["search_query"], "widget")
        # Result keys are always present, regardless of matches
        self.assertIn("product_results", response.context)
        self.assertIn("category_results", response.context)
        self.assertIn("location_results", response.context)

    @patch("inventory.views.get_search_backend")
    def test_search_finds_product_by_name(self, mock_get_backend):
        create_product(sku="SRCH-001", name="Wireless Mouse")
        mock_backend = mock_get_backend.return_value
        mock_backend.search.side_effect = lambda q, qs: (
            qs.filter(name__icontains=q)
            if qs.model == Product
            else qs.none()
        )
        response = self.client.get(self.url, {"q": "Wireless Mouse"})
        self.assertEqual(response.context["search_query"], "Wireless Mouse")
        product_results = list(response.context["product_results"])
        skus = [p.sku for p in product_results]
        self.assertIn("SRCH-001", skus)

    @patch("inventory.views.get_search_backend")
    def test_search_finds_category(self, mock_get_backend):
        create_category(name="Electronics", slug="srch-electronics")
        mock_backend = mock_get_backend.return_value
        mock_backend.search.side_effect = lambda q, qs: (
            qs.filter(name__icontains=q)
            if qs.model == Category
            else qs.none()
        )
        response = self.client.get(self.url, {"q": "Electronics"})
        category_results = list(response.context["category_results"])
        names = [c.name for c in category_results]
        self.assertIn("Electronics", names)

    @patch("inventory.views.get_search_backend")
    def test_search_finds_location(self, mock_get_backend):
        create_location(name="Main Warehouse")
        mock_backend = mock_get_backend.return_value
        mock_backend.search.side_effect = lambda q, qs: (
            qs.filter(name__icontains=q)
            if qs.model == StockLocation
            else qs.none()
        )
        response = self.client.get(self.url, {"q": "Main Warehouse"})
        location_results = list(response.context["location_results"])
        names = [loc.name for loc in location_results]
        self.assertIn("Main Warehouse", names)

    @patch("inventory.views.get_search_backend")
    def test_search_excludes_inactive_products(self, mock_get_backend):
        create_product(sku="INACTIVE-SRCH", name="Old Item", is_active=False)
        mock_backend = mock_get_backend.return_value
        # Simulate backend returning all matches — view pre-filters is_active=True
        mock_backend.search.side_effect = lambda q, qs: qs.filter(
            name__icontains=q,
        )
        response = self.client.get(self.url, {"q": "Old Item"})
        product_results = list(response.context["product_results"])
        skus = [p.sku for p in product_results]
        self.assertNotIn("INACTIVE-SRCH", skus)
