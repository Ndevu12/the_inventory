"""Smoke tests for TranslatableMixin models + wagtail-localize field config (I18N-06).

wagtail-localize does not provide a translation-specific panel; use normal ``FieldPanel``
everywhere. What gets translated is driven by ``get_translatable_fields()`` and optional
``override_translatable_fields`` / ``translatable_fields`` on the model.
"""

from django.test import TestCase
from wagtail_localize.fields import (
    SynchronizedField,
    TranslatableField,
    get_translatable_fields,
)

from inventory.models.category import Category
from inventory.models.product import Product
from procurement.models.supplier import Supplier
from sales.models.customer import Customer


class TranslatableMixinModelPanelsTests(TestCase):
    """Standard Wagtail panels bind; localize metadata matches overrides."""

    def test_inventory_and_domain_models_tabbed_panels_bind(self):
        for model in (Product, Category, Supplier, Customer):
            with self.subTest(model=model.__name__):
                tabbed = model.panels[0]
                bound = tabbed.bind_to_model(model)
                opts = bound.get_form_options()
                self.assertTrue(opts.get("fields") or opts.get("formsets"))

    def test_override_translatable_fields_match_wagtail_localize_1x(self):
        """Codes/SKUs are synchronized; user-facing text uses default translation.

        wagtail-localize 1.x has no ``TranslatableFieldPanel``—behavior is defined
        here and via ``get_translatable_fields()``, not admin panel classes.
        """
        product_fields = {f.field_name: f for f in get_translatable_fields(Product)}
        self.assertIsInstance(product_fields["sku"], SynchronizedField)
        self.assertIsInstance(product_fields["name"], TranslatableField)
        self.assertIsInstance(product_fields["description"], TranslatableField)

        supplier_fields = {f.field_name: f for f in get_translatable_fields(Supplier)}
        self.assertIsInstance(supplier_fields["code"], SynchronizedField)
        self.assertIsInstance(supplier_fields["name"], TranslatableField)

        customer_fields = {f.field_name: f for f in get_translatable_fields(Customer)}
        self.assertIsInstance(customer_fields["code"], SynchronizedField)
        self.assertIsInstance(customer_fields["name"], TranslatableField)

        category_fields = {f.field_name: f for f in get_translatable_fields(Category)}
        self.assertIsInstance(category_fields["name"], TranslatableField)
        self.assertIsInstance(category_fields["description"], TranslatableField)
        self.assertIsInstance(category_fields["slug"], TranslatableField)
