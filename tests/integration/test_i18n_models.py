"""Integration tests for Wagtail translatable inventory catalog models (I18N-15)."""

from django.core.exceptions import ValidationError
from django.test import TestCase
from wagtail.models import Locale

from inventory.models import Category, Product
from inventory.services.localization import copy_catalog_row_for_locale
from tests.fixtures.factories import create_category, create_product, create_tenant
from tenants.context import set_current_tenant


class ProductTranslationIntegrationTests(TestCase):
    """Translation graph: same ``translation_key``, locale-specific rows."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        self.tenant = create_tenant(name="I18N Integration Tenant")
        set_current_tenant(self.tenant)
        self.fr_locale = Locale.objects.get(language_code="fr")

    def test_copy_for_translation_links_and_get_translation_or_none(self):
        product_en = create_product(
            sku="INT-SKU", name="English", tenant=self.tenant,
        )
        product_fr = product_en.copy_for_translation(self.fr_locale)
        product_fr.name = "Français"
        product_fr.save()

        self.assertEqual(product_en.translation_key, product_fr.translation_key)
        self.assertNotEqual(product_en.pk, product_fr.pk)
        self.assertEqual(
            product_en.get_translation_or_none(self.fr_locale).pk,
            product_fr.pk,
        )
        self.assertEqual(product_fr.get_translation_or_none(product_en.locale).pk, product_en.pk)

    def test_list_filter_canonical_locale_is_enforced_at_api_layer(self):
        """Canonical list behavior is covered in API tests; models allow all locale rows."""
        product_en = create_product(sku="INT-SKU2", tenant=self.tenant)
        product_fr = product_en.copy_for_translation(self.fr_locale)
        product_fr.name = "FR"
        product_fr.save()

        qs = Product.objects.filter(tenant=self.tenant)
        self.assertEqual(qs.count(), 2)


class CategoryTranslationIntegrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        self.tenant = create_tenant(name="I18N Category Tenant")
        set_current_tenant(self.tenant)
        self.fr_locale = Locale.objects.get(language_code="fr")

    def test_category_translation_shares_translation_key(self):
        cat_en = create_category(name="Books", slug="books-int", tenant=self.tenant)
        cat_fr = copy_catalog_row_for_locale(cat_en, self.fr_locale)
        cat_fr.name = "Livres"
        cat_fr.slug = "livres-int"
        cat_fr.save()

        self.assertEqual(cat_en.translation_key, cat_fr.translation_key)
        self.assertIsInstance(cat_en, Category)
        self.assertEqual(
            cat_en.get_translation_or_none(self.fr_locale).name,
            "Livres",
        )

    def test_nested_category_translation_save_uses_translated_parent(self):
        """Mirrors wagtail-localize snippet translate: copy_for_translation then save()."""
        cat_en = create_category(name="Root", slug="root-nested-int", tenant=self.tenant)
        copy_catalog_row_for_locale(cat_en, self.fr_locale)
        child_en = cat_en.add_child(
            name="Child",
            slug="child-nested-int",
            tenant=self.tenant,
        )
        parent_fr = cat_en.get_translation(self.fr_locale)
        child_fr = child_en.copy_for_translation(self.fr_locale)
        child_fr.save()
        self.assertEqual(child_fr.get_parent().pk, parent_fr.pk)

    def test_nested_category_translation_requires_parent_locale_first(self):
        cat_en = create_category(name="Root", slug="root-req-parent", tenant=self.tenant)
        child_en = cat_en.add_child(
            name="Child",
            slug="child-req-parent",
            tenant=self.tenant,
        )
        child_fr = child_en.copy_for_translation(self.fr_locale)
        with self.assertRaises(ValidationError):
            child_fr.save()
