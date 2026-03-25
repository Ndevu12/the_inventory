"""Catalog models are registered as Wagtail snippets for admin + wagtail-localize."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from wagtail.models import Locale
from wagtail.snippets.models import get_snippet_models
from wagtail_localize import wagtail_hooks as localize_hooks

from inventory.models import Category, Product
from procurement.models import Supplier
from sales.models import Customer
from tests.fixtures.factories import create_product, create_tenant

User = get_user_model()


class CatalogSnippetRegistrationTests(TestCase):
    def test_translatable_catalog_models_are_snippets(self):
        registered = get_snippet_models()
        for model in (Product, Category, Supplier, Customer):
            with self.subTest(model=model.__name__):
                self.assertIn(model, registered)
                self.assertIsNotNone(getattr(model, "snippet_viewset", None))


class CatalogSnippetTranslateUIHookTests(TestCase):
    """wagtail-localize listing **Translate** when a second Locale exists (admin UX)."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    @staticmethod
    def _submit_translation_perm():
        return Permission.objects.get(
            content_type__app_label="wagtail_localize",
            codename="submit_translation",
        )

    def test_translate_snippet_listing_button_when_perm_and_extra_locale(self):
        tenant = create_tenant()
        user = User.objects.create_user("snippet_translate", password="pass")
        user.user_permissions.add(self._submit_translation_perm())
        product = create_product(sku="SNIP-TX", name="Widget", tenant=tenant)
        buttons = list(
            localize_hooks.register_snippet_listing_buttons(product, user),
        )
        labels = [str(getattr(b, "label", b)) for b in buttons]
        self.assertIn("Translate", labels)

    def test_no_translate_listing_button_without_perm(self):
        tenant = create_tenant()
        user = User.objects.create_user("snippet_no_tx", password="pass")
        product = create_product(sku="SNIP-NO", name="Other", tenant=tenant)
        buttons = list(
            localize_hooks.register_snippet_listing_buttons(product, user),
        )
        self.assertEqual(buttons, [])
