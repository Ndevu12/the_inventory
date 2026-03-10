"""Unit tests for Product, ProductImage, ProductTag, and ProductQuerySet."""

from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from inventory.models import Category, Product, UnitOfMeasure

from ..factories import (
    create_category,
    create_location,
    create_product,
    create_stock_record,
)


class ProductCreationTests(TestCase):
    """Test Product creation with various field combinations."""

    def test_create_product_with_defaults(self):
        product = create_product()
        self.assertEqual(product.sku, "TEST-001")
        self.assertEqual(product.name, "Test Product")
        self.assertEqual(product.unit_of_measure, UnitOfMeasure.PIECES)
        self.assertEqual(product.unit_cost, Decimal("10.00"))
        self.assertEqual(product.reorder_point, 5)
        self.assertTrue(product.is_active)

    def test_create_product_with_all_fields(self):
        category = create_category(slug="prod-cat")
        product = create_product(
            sku="FULL-001",
            name="Full Product",
            category=category,
            unit_of_measure=UnitOfMeasure.KILOGRAMS,
            unit_cost=Decimal("25.50"),
            reorder_point=10,
            description="<p>A full product</p>",
        )
        self.assertEqual(product.category, category)
        self.assertEqual(product.unit_of_measure, UnitOfMeasure.KILOGRAMS)
        self.assertEqual(product.unit_cost, Decimal("25.50"))

    def test_product_without_category(self):
        product = create_product(sku="NO-CAT", category=None)
        self.assertIsNone(product.category)

    def test_create_inactive_product(self):
        product = create_product(sku="INACTIVE", is_active=False)
        self.assertFalse(product.is_active)


class ProductSkuUniquenessTests(TestCase):
    """Test SKU uniqueness constraint."""

    def test_duplicate_sku_raises_integrity_error(self):
        create_product(sku="DUP-001")
        with self.assertRaises(IntegrityError):
            create_product(sku="DUP-001", name="Another Product")

    def test_different_skus_allowed(self):
        p1 = create_product(sku="SKU-A")
        p2 = create_product(sku="SKU-B")
        self.assertNotEqual(p1.pk, p2.pk)


class ProductCategoryFKTests(TestCase):
    """Test Category FK behavior."""

    def test_category_set_null_on_delete(self):
        category = create_category(slug="deletable")
        product = create_product(sku="FK-TEST", category=category)
        category_pk = category.pk
        # Delete the category node from treebeard
        Category.objects.filter(pk=category_pk).delete()
        product.refresh_from_db()
        self.assertIsNone(product.category)


class ProductStrTests(TestCase):
    """Test __str__ representation."""

    def test_str_format(self):
        product = create_product(sku="WDG-100", name="Widget")
        self.assertEqual(str(product), "WDG-100 — Widget")


class UnitOfMeasureTests(TestCase):
    """Test UnitOfMeasure enum values."""

    def test_all_choices_exist(self):
        labels = dict(UnitOfMeasure.choices)
        self.assertIn("pcs", labels)
        self.assertIn("kg", labels)
        self.assertIn("lt", labels)
        self.assertIn("m", labels)
        self.assertIn("box", labels)
        self.assertIn("pack", labels)

    def test_choice_labels(self):
        self.assertEqual(UnitOfMeasure.PIECES.label, "Pieces")
        self.assertEqual(UnitOfMeasure.KILOGRAMS.label, "Kilograms")
        self.assertEqual(UnitOfMeasure.LITERS.label, "Liters")


class ProductQuerySetLowStockTests(TestCase):
    """Test ProductQuerySet.low_stock() custom manager method."""

    def setUp(self):
        self.location = create_location(name="Warehouse")
        self.low_product = create_product(
            sku="LOW-001", name="Low Stock Item", reorder_point=10,
        )
        create_stock_record(
            product=self.low_product, location=self.location, quantity=3,
        )
        self.ok_product = create_product(
            sku="OK-001", name="OK Stock Item", reorder_point=5,
        )
        create_stock_record(
            product=self.ok_product, location=self.location, quantity=50,
        )

    def test_low_stock_returns_below_reorder_point(self):
        qs = Product.objects.low_stock()
        self.assertIn(self.low_product, qs)
        self.assertNotIn(self.ok_product, qs)

    def test_low_stock_excludes_zero_reorder_point(self):
        no_alert = create_product(
            sku="NO-ALERT", name="No Alert", reorder_point=0,
        )
        create_stock_record(
            product=no_alert, location=self.location, quantity=0,
        )
        qs = Product.objects.low_stock()
        self.assertNotIn(no_alert, qs)

    def test_low_stock_includes_at_reorder_point(self):
        """Product at exactly the reorder point IS low stock."""
        exact = create_product(sku="EXACT-001", reorder_point=10)
        create_stock_record(
            product=exact, location=self.location, quantity=10,
        )
        qs = Product.objects.low_stock()
        self.assertIn(exact, qs)


class ProductQuerySetOutOfStockTests(TestCase):
    """Test ProductQuerySet.out_of_stock() custom manager method."""

    def test_out_of_stock_returns_zero_quantity(self):
        location = create_location(name="Warehouse")
        product = create_product(sku="OOS-001")
        create_stock_record(product=product, location=location, quantity=0)
        qs = Product.objects.out_of_stock()
        self.assertIn(product, qs)

    def test_out_of_stock_excludes_positive_quantity(self):
        location = create_location(name="Warehouse")
        product = create_product(sku="IN-001")
        create_stock_record(product=product, location=location, quantity=10)
        qs = Product.objects.out_of_stock()
        self.assertNotIn(product, qs)


class ProductQuerySetInStockTests(TestCase):
    """Test ProductQuerySet.in_stock() custom manager method."""

    def test_in_stock_returns_above_reorder_point(self):
        location = create_location(name="Warehouse")
        product = create_product(sku="IS-001", reorder_point=5)
        create_stock_record(product=product, location=location, quantity=50)
        qs = Product.objects.in_stock()
        self.assertIn(product, qs)

    def test_in_stock_excludes_low_stock(self):
        location = create_location(name="Warehouse")
        product = create_product(sku="IS-LOW", reorder_point=10)
        create_stock_record(product=product, location=location, quantity=3)
        qs = Product.objects.in_stock()
        self.assertNotIn(product, qs)


class ProductTagTests(TestCase):
    """Test tagging functionality on Product."""

    def test_add_tags_to_product(self):
        product = create_product(sku="TAG-001")
        product.tags.add("fragile", "heavy")
        self.assertEqual(product.tags.count(), 2)
        tag_names = list(product.tags.names())
        self.assertIn("fragile", tag_names)
        self.assertIn("heavy", tag_names)

    def test_remove_tag_from_product(self):
        product = create_product(sku="TAG-002")
        product.tags.add("temporary")
        product.tags.remove("temporary")
        self.assertEqual(product.tags.count(), 0)
