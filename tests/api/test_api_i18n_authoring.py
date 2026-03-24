"""Tests for translatable catalog POST/PATCH authoring (I18N-16)."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from wagtail.models import Locale

from inventory.models import Product
from procurement.models import Supplier
from sales.models import Customer
from tenants.context import set_current_tenant
from tenants.models import TenantRole
from tests.fixtures.factories import create_category, create_product, create_tenant, create_tenant_membership

User = get_user_model()


class I18NAuthoringSetupMixin:
    def setUp(self):
        self.tenant = create_tenant(name="I18N Authoring Tenant")
        self.user = User.objects.create_user(
            username="i18nauthor",
            password="testpass123",
            is_staff=True,
        )
        create_tenant_membership(self.tenant, self.user, role=TenantRole.MANAGER)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        set_current_tenant(self.tenant)


class ProductAuthoringAPITests(I18NAuthoringSetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        self.fr = Locale.objects.get(language_code="fr")
        self.en = Locale.objects.get_for_language("en")

    def test_post_without_language_uses_canonical_locale(self):
        response = self.client.post(
            "/api/v1/products/",
            {
                "sku": "AUTH-P1",
                "name": "English",
                "unit_of_measure": "pcs",
                "unit_cost": "10.00",
                "reorder_point": 0,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        p = Product.objects.get(pk=response.data["id"])
        self.assertEqual(p.locale_id, self.en.id)

    def test_post_french_requires_translation_of(self):
        response = self.client.post(
            "/api/v1/products/?language=fr",
            {
                "sku": "AUTH-P2",
                "name": "Français",
                "unit_of_measure": "pcs",
                "unit_cost": "10.00",
                "reorder_point": 0,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("translation_of", response.data)

    def test_post_french_creates_linked_translation(self):
        cat = create_category(tenant=self.tenant)
        p_en = create_product(
            sku="AUTH-P3",
            name="Source",
            category=cat,
            tenant=self.tenant,
        )
        response = self.client.post(
            f"/api/v1/products/?language=fr",
            {
                "translation_of": p_en.pk,
                "sku": p_en.sku,
                "name": "Produit FR",
                "category": cat.pk,
                "unit_of_measure": "pcs",
                "unit_cost": "10.00",
                "reorder_point": 0,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        p_fr = Product.objects.get(pk=response.data["id"])
        self.assertEqual(p_fr.locale_id, self.fr.id)
        self.assertEqual(p_fr.translation_key, p_en.translation_key)
        self.assertEqual(p_fr.name, "Produit FR")

    def test_patch_with_language_updates_translation_row(self):
        cat = create_category(tenant=self.tenant)
        p_en = create_product(sku="AUTH-P4", name="En", category=cat, tenant=self.tenant)
        p_fr = p_en.copy_for_translation(self.fr)
        p_fr.name = "Ancien"
        p_fr.save()
        response = self.client.patch(
            f"/api/v1/products/{p_en.pk}/?language=fr",
            {"name": "Nouveau"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        p_fr.refresh_from_db()
        self.assertEqual(p_fr.name, "Nouveau")
        p_en.refresh_from_db()
        self.assertEqual(p_en.name, "En")


class SupplierCustomerAuthoringAPITests(I18NAuthoringSetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        self.fr = Locale.objects.get(language_code="fr")
        self.en = Locale.objects.get_for_language("en")

    def test_supplier_post_french_linked(self):
        s_en = Supplier.objects.create(
            code="SUP-AUTH",
            name="Supplier EN",
            tenant=self.tenant,
            locale=self.en,
        )
        response = self.client.post(
            "/api/v1/suppliers/?language=fr",
            {
                "translation_of": s_en.pk,
                "code": s_en.code,
                "name": "Fournisseur FR",
                "lead_time_days": 1,
                "payment_terms": "net_30",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        s_fr = Supplier.objects.get(pk=response.data["id"])
        self.assertEqual(s_fr.locale_id, self.fr.id)
        self.assertEqual(s_fr.translation_key, s_en.translation_key)

    def test_customer_patch_language_creates_translation(self):
        c_en = Customer.objects.create(
            code="CUST-AUTH",
            name="Customer EN",
            tenant=self.tenant,
            locale=self.en,
        )
        response = self.client.patch(
            f"/api/v1/customers/{c_en.pk}/?language=fr",
            {"name": "Client FR"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        c_fr = Customer.objects.get(
            translation_key=c_en.translation_key,
            locale_id=self.fr.id,
        )
        self.assertEqual(c_fr.name, "Client FR")


class CategoryAuthoringAPITests(I18NAuthoringSetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        self.fr = Locale.objects.get(language_code="fr")
        self.en = Locale.objects.get_for_language("en")

    def test_post_canonical_category_add_root(self):
        response = self.client.post(
            "/api/v1/categories/",
            {
                "name": "Root API",
                "slug": "root-api-cat",
                "description": "",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        from inventory.models import Category

        c = Category.objects.get(pk=response.data["id"])
        self.assertEqual(c.locale_id, self.en.id)
        self.assertTrue(c.is_root())

    def test_post_french_category_linked(self):
        from inventory.models import Category

        c_en = create_category(name="Books EN", slug="books-en-auth", tenant=self.tenant)
        response = self.client.post(
            "/api/v1/categories/?language=fr",
            {
                "translation_of": c_en.pk,
                "name": "Livres FR",
                "slug": "livres-fr-auth",
                "description": "",
                "is_active": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        c_fr = Category.objects.get(pk=response.data["id"])
        self.assertEqual(c_fr.locale_id, self.fr.id)
        self.assertEqual(c_fr.translation_key, c_en.translation_key)
