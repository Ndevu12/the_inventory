"""Tests for inventory filtersets and custom filters."""

from django.test import TestCase

from inventory.filters import ProductFilterSet, StockStatusFilter
from inventory.models import Product

from .factories import (
    create_category,
    create_location,
    create_product,
    create_stock_record,
)


class StockStatusFilterTests(TestCase):
    """Test the custom StockStatusFilter choice filter."""

    def setUp(self):
        self.location = create_location(name="Warehouse")

        # Low-stock product: quantity (3) < reorder_point (10)
        self.low_product = create_product(
            sku="FLT-LOW", name="Low Stock", reorder_point=10,
        )
        create_stock_record(
            product=self.low_product, location=self.location, quantity=3,
        )

        # In-stock product: quantity (50) > reorder_point (5)
        self.ok_product = create_product(
            sku="FLT-OK", name="In Stock", reorder_point=5,
        )
        create_stock_record(
            product=self.ok_product, location=self.location, quantity=50,
        )

        # Out-of-stock product: quantity 0
        self.oos_product = create_product(
            sku="FLT-OOS", name="Out of Stock", reorder_point=5,
        )
        create_stock_record(
            product=self.oos_product, location=self.location, quantity=0,
        )

    def test_filter_low_stock(self):
        f = StockStatusFilter()
        qs = f.filter(Product.objects.all(), "low")
        self.assertIn(self.low_product, qs)
        self.assertNotIn(self.ok_product, qs)

    def test_filter_in_stock(self):
        f = StockStatusFilter()
        qs = f.filter(Product.objects.all(), "in_stock")
        self.assertIn(self.ok_product, qs)
        self.assertNotIn(self.low_product, qs)

    def test_filter_out_of_stock(self):
        f = StockStatusFilter()
        qs = f.filter(Product.objects.all(), "out_of_stock")
        self.assertIn(self.oos_product, qs)
        self.assertNotIn(self.ok_product, qs)

    def test_filter_empty_value_returns_all(self):
        f = StockStatusFilter()
        qs = f.filter(Product.objects.all(), "")
        self.assertEqual(qs.count(), Product.objects.count())

    def test_filter_none_value_returns_all(self):
        f = StockStatusFilter()
        qs = f.filter(Product.objects.all(), None)
        self.assertEqual(qs.count(), Product.objects.count())


class ProductFilterSetCategoryTests(TestCase):
    """Test ProductFilterSet category filter."""

    def test_filter_by_category(self):
        cat_a = create_category(name="Electronics", slug="electronics")
        cat_b = create_category(name="Clothing", slug="clothing")
        p_a = create_product(sku="CAT-A", category=cat_a)
        create_product(sku="CAT-B", category=cat_b)

        fs = ProductFilterSet(
            {"category": cat_a.pk}, queryset=Product.objects.all(),
        )
        self.assertIn(p_a, fs.qs)
        self.assertEqual(fs.qs.count(), 1)


class ProductFilterSetActiveTests(TestCase):
    """Test ProductFilterSet is_active filter."""

    def test_filter_active_only(self):
        create_product(sku="ACT-001", is_active=True)
        create_product(sku="ACT-002", is_active=False)

        fs = ProductFilterSet(
            {"is_active": True}, queryset=Product.objects.all(),
        )
        self.assertEqual(fs.qs.count(), 1)
        self.assertEqual(fs.qs.first().sku, "ACT-001")


class ProductFilterSetLocationTests(TestCase):
    """Test ProductFilterSet location filter."""

    def test_filter_by_location(self):
        loc_a = create_location(name="Location A")
        loc_b = create_location(name="Location B")
        p1 = create_product(sku="LOC-001")
        p2 = create_product(sku="LOC-002")
        create_stock_record(product=p1, location=loc_a, quantity=10)
        create_stock_record(product=p2, location=loc_b, quantity=5)

        fs = ProductFilterSet(
            {"location": loc_a.pk}, queryset=Product.objects.all(),
        )
        self.assertIn(p1, fs.qs)
        self.assertNotIn(p2, fs.qs)
