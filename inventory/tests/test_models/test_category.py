"""Unit tests for the Category model."""

from django.db import IntegrityError
from django.test import TestCase

from inventory.models import Category

from ..factories import create_category


class CategoryCreationTests(TestCase):
    """Test Category creation and field defaults."""

    def test_create_root_category(self):
        category = create_category(name="Electronics", slug="electronics")
        self.assertEqual(category.name, "Electronics")
        self.assertEqual(category.slug, "electronics")
        self.assertTrue(category.is_active)
        self.assertEqual(category.description, "")

    def test_create_category_with_description(self):
        category = create_category(
            name="Tools",
            slug="tools",
            description="Hand and power tools",
        )
        self.assertEqual(category.description, "Hand and power tools")

    def test_is_active_defaults_to_true(self):
        category = create_category(slug="active-test")
        self.assertTrue(category.is_active)

    def test_create_inactive_category(self):
        category = create_category(slug="inactive", is_active=False)
        self.assertFalse(category.is_active)


class CategorySlugUniquenessTests(TestCase):
    """Test slug uniqueness constraint."""

    def test_duplicate_slug_raises_integrity_error(self):
        create_category(name="First", slug="unique-slug")
        with self.assertRaises(IntegrityError):
            create_category(name="Second", slug="unique-slug")

    def test_different_slugs_allowed(self):
        cat1 = create_category(name="First", slug="first")
        cat2 = create_category(name="Second", slug="second")
        self.assertNotEqual(cat1.pk, cat2.pk)


class CategoryTreeTests(TestCase):
    """Test treebeard hierarchy operations."""

    def test_add_child_category(self):
        parent = create_category(name="Electronics", slug="electronics")
        child = parent.add_child(name="Phones", slug="phones")
        self.assertEqual(child.get_parent().pk, parent.pk)

    def test_root_has_no_parent(self):
        root = create_category(slug="root-test")
        self.assertIsNone(root.get_parent())

    def test_get_children(self):
        parent = create_category(name="Clothing", slug="clothing")
        parent.add_child(name="Shirts", slug="shirts")
        parent.add_child(name="Pants", slug="pants")
        self.assertEqual(parent.get_children().count(), 2)

    def test_nested_depth(self):
        root = create_category(name="Root", slug="root")
        child = root.add_child(name="Child", slug="child")
        grandchild = child.add_child(name="Grandchild", slug="grandchild")
        self.assertEqual(grandchild.get_depth(), 3)


class CategoryStrTests(TestCase):
    """Test __str__ representation."""

    def test_str_returns_name(self):
        category = create_category(name="My Category", slug="my-category")
        self.assertEqual(str(category), "My Category")


class CategoryMetaTests(TestCase):
    """Test model Meta options."""

    def test_verbose_name_plural(self):
        self.assertEqual(Category._meta.verbose_name_plural, "categories")


class CategorySaveOverrideTests(TestCase):
    """Test save() override for treebeard MP_Node creation."""

    def test_save_creates_root_node_with_depth(self):
        """Direct save() on new instance should create a root node via add_root()."""
        category = Category(name="Direct Save", slug="direct-save")
        category.save()
        self.assertEqual(category.depth, 1)
        self.assertIsNotNone(category.path)
        self.assertEqual(category.numchild, 0)

    def test_save_multiple_root_nodes(self):
        """Multiple save() calls should create distinct root nodes, not duplicates."""
        cat1 = Category(name="Root One", slug="root-one")
        cat1.save()
        cat2 = Category(name="Root Two", slug="root-two")
        cat2.save()
        self.assertEqual(cat1.depth, 1)
        self.assertEqual(cat2.depth, 1)
        self.assertNotEqual(cat1.pk, cat2.pk)
        self.assertEqual(Category.objects.count(), 2)

    def test_update_existing_category_via_save(self):
        """Updating an existing category via save() should not create a duplicate."""
        category = create_category(name="Original", slug="original")
        original_pk = category.pk
        category.name = "Updated"
        category.save()
        self.assertEqual(category.pk, original_pk)
        self.assertEqual(category.depth, 1)
        # Verify no duplicates created
        self.assertEqual(Category.objects.filter(pk=original_pk).count(), 1)
