"""API ``?language=`` resolution, tenant defaults, and translatable writes (I18N-15)."""

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from wagtail.models import Locale

from api.language import resolve_display_language_code, resolve_write_language_code
from api.serializers.inventory import ProductSerializer
from tests.api.test_inventory_api import APISetupMixin
from tests.fixtures.factories import (
    create_customer,
    create_membership,
    create_product,
    create_purchase_order,
    create_purchase_order_line,
    create_sales_order,
    create_sales_order_line,
    create_supplier,
    create_tenant,
    create_user,
)
from tenants.models import TenantRole
from tenants.context import set_current_tenant

User = get_user_model()


class ResolveDisplayLanguageCodeTests(APITestCase):
    def test_query_param_wins(self):
        tenant = SimpleNamespace(preferred_language="en")
        request = RequestFactory().get("/api/v1/products/", {"language": "fr"})
        self.assertEqual(resolve_display_language_code(request, tenant), "fr")

    def test_invalid_query_param_raises(self):
        tenant = SimpleNamespace(preferred_language="en")
        request = RequestFactory().get("/api/v1/products/", {"language": "xx-invalid"})
        with self.assertRaises(ValidationError):
            resolve_display_language_code(request, tenant)

    def test_accept_language_when_tenant_pref_empty(self):
        tenant = SimpleNamespace(preferred_language="")
        request = RequestFactory().get(
            "/api/v1/products/",
            HTTP_ACCEPT_LANGUAGE="fr-fr,fr;q=0.9,en;q=0.8",
        )
        self.assertEqual(resolve_display_language_code(request, tenant), "fr")


class ResolveWriteLanguageCodeTests(APITestCase):
    def test_query_param_wins(self):
        tenant = SimpleNamespace(preferred_language="en")
        request = RequestFactory().patch("/api/v1/products/1/?language=fr")
        self.assertEqual(resolve_write_language_code(request, tenant), "fr")

    def test_without_query_uses_canonical_not_accept_language(self):
        tenant = SimpleNamespace(preferred_language="en")
        request = RequestFactory().patch(
            "/api/v1/products/1/",
            HTTP_ACCEPT_LANGUAGE="fr-fr,fr;q=0.9,en;q=0.8",
        )
        self.assertEqual(resolve_write_language_code(request, tenant), "en")

    def test_without_query_uses_tenant_preferred(self):
        tenant = SimpleNamespace(preferred_language="fr")
        request = RequestFactory().patch("/api/v1/products/1/")
        self.assertEqual(resolve_write_language_code(request, tenant), "fr")

    def test_invalid_query_param_raises(self):
        tenant = SimpleNamespace(preferred_language="en")
        request = RequestFactory().patch("/api/v1/products/1/?language=xx-invalid")
        with self.assertRaises(ValidationError):
            resolve_write_language_code(request, tenant)


class ProductLanguageAPITests(APISetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        fr_locale = Locale.objects.get(language_code="fr")
        self.p_en = create_product(sku="LANG-SKU", name="English widget", tenant=self.tenant)
        p_fr = self.p_en.copy_for_translation(fr_locale)
        p_fr.name = "Gadget français"
        p_fr.save()

    def test_list_products_language_fr_overlays_name(self):
        response = self.client.get("/api/v1/products/", {"language": "fr"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        row = response.data["results"][0]
        self.assertEqual(row["id"], self.p_en.pk)
        self.assertEqual(row["sku"], "LANG-SKU")
        self.assertEqual(row["name"], "Gadget français")

    def test_list_products_without_language_uses_tenant_preferred(self):
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = response.data["results"][0]
        self.assertEqual(row["name"], "English widget")

    def test_retrieve_product_with_language_fr(self):
        response = self.client.get(
            f"/api/v1/products/{self.p_en.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Gadget français")

    def test_invalid_language_returns_400(self):
        response = self.client.get("/api/v1/products/", {"language": "not-a-locale"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SupplierLanguageAPITests(APISetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        fr_locale = Locale.objects.get(language_code="fr")
        self.s_en = create_supplier(
            tenant=self.tenant,
            code="SUP-LANG",
            name="Acme Supplies",
        )
        s_fr = self.s_en.copy_for_translation(fr_locale)
        s_fr.name = "Fournitures Acme"
        s_fr.save()

    def test_list_suppliers_language_fr(self):
        response = self.client.get("/api/v1/suppliers/", {"language": "fr"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Fournitures Acme")


class CustomerLanguageAPITests(APISetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        fr_locale = Locale.objects.get(language_code="fr")
        self.c_en = create_customer(
            tenant=self.tenant,
            code="CUST-LANG",
            name="English customer",
        )
        c_fr = self.c_en.copy_for_translation(fr_locale)
        c_fr.name = "Client français"
        c_fr.save()

    def test_list_customers_language_fr(self):
        response = self.client.get("/api/v1/customers/", {"language": "fr"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Client français")


class ProductSerializerLanguageContextTests(TestCase):
    """Serializer returns overlay strings when only ``language`` is in context (I18N-11)."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        self.tenant = create_tenant(name="Serializer I18N Tenant")
        set_current_tenant(self.tenant)
        fr_locale = Locale.objects.get(language_code="fr")
        self.p_en = create_product(sku="SER-I18N", name="English line", tenant=self.tenant)
        p_fr = self.p_en.copy_for_translation(fr_locale)
        p_fr.name = "Ligne française"
        p_fr.save()

    def test_context_language_fr_overlays_name(self):
        data = ProductSerializer(
            self.p_en,
            context={"language": "fr"},
        ).data
        self.assertEqual(data["name"], "Ligne française")


class PurchaseOrderNestedLanguageAPITests(APISetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        fr_locale = Locale.objects.get(language_code="fr")
        self.product = create_product(sku="PO-I18N", name="Prod EN", tenant=self.tenant)
        p_fr = self.product.copy_for_translation(fr_locale)
        p_fr.name = "Produit FR"
        p_fr.save()
        self.supplier = create_supplier(
            tenant=self.tenant, code="PO-SUP-I18N", name="Sup EN",
        )
        s_fr = self.supplier.copy_for_translation(fr_locale)
        s_fr.name = "Fournisseur FR"
        s_fr.save()
        self.po = create_purchase_order(supplier=self.supplier, tenant=self.tenant)
        create_purchase_order_line(self.po, self.product)

    def test_retrieve_po_language_fr_nested_names(self):
        response = self.client.get(
            f"/api/v1/purchase-orders/{self.po.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["supplier_name"], "Fournisseur FR")
        self.assertEqual(len(response.data["lines"]), 1)
        self.assertEqual(response.data["lines"][0]["product_name"], "Produit FR")


class SalesOrderNestedLanguageAPITests(APISetupMixin, APITestCase):
    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        fr_locale = Locale.objects.get(language_code="fr")
        self.product = create_product(sku="SO-I18N", name="Prod EN", tenant=self.tenant)
        p_fr = self.product.copy_for_translation(fr_locale)
        p_fr.name = "Produit FR"
        p_fr.save()
        self.customer = create_customer(
            tenant=self.tenant, code="SO-CUST-I18N", name="Cust EN",
        )
        c_fr = self.customer.copy_for_translation(fr_locale)
        c_fr.name = "Client FR"
        c_fr.save()
        self.so = create_sales_order(customer=self.customer, tenant=self.tenant)
        create_sales_order_line(self.so, self.product)

    def test_retrieve_so_language_fr_nested_names(self):
        response = self.client.get(
            f"/api/v1/sales-orders/{self.so.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["customer_name"], "Client FR")
        self.assertEqual(len(response.data["lines"]), 1)
        self.assertEqual(response.data["lines"][0]["product_name"], "Produit FR")


class TenantPreferredLanguageAPITests(APITestCase):
    """Two tenants with different ``preferred_language`` see correct default strings."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")
        Locale.objects.get_or_create(language_code="es")

    def setUp(self):
        self.tenant_fr = create_tenant(
            name="Tenant FR", slug="tenant-fr-pref", preferred_language="fr",
        )
        self.tenant_es = create_tenant(
            name="Tenant ES", slug="tenant-es-pref", preferred_language="es",
        )
        set_current_tenant(self.tenant_fr)
        fr_loc = Locale.objects.get(language_code="fr")
        es_loc = Locale.objects.get(language_code="es")

        self.user = create_user(username="i18n-two-tenant-user")
        create_membership(
            tenant=self.tenant_fr, user=self.user, role=TenantRole.COORDINATOR, is_default=True,
        )
        create_membership(
            tenant=self.tenant_es, user=self.user, role=TenantRole.MANAGER, is_default=False,
        )

        self.p_fr = create_product(
            sku="DUAL-SKU",
            name="Nom français",
            tenant=self.tenant_fr,
            locale=fr_loc,
        )
        p_fr_en = self.p_fr.copy_for_translation(Locale.get_default())
        p_fr_en.name = "French name in English row"
        p_fr_en.save()

        set_current_tenant(self.tenant_es)
        self.p_es = create_product(
            sku="DUAL-SKU-ES",
            name="Nombre español",
            tenant=self.tenant_es,
            locale=es_loc,
        )
        p_es_en = self.p_es.copy_for_translation(Locale.get_default())
        p_es_en.name = "Spanish name in English row"
        p_es_en.save()

        from rest_framework.authtoken.models import Token

        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_tenant_fr_default_list_is_french(self):
        response = self.client.get(
            "/api/v1/products/",
            HTTP_X_TENANT="tenant-fr-pref",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Nom français")

    def test_tenant_es_default_list_is_spanish(self):
        response = self.client.get(
            "/api/v1/products/",
            HTTP_X_TENANT="tenant-es-pref",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Nombre español")

    def test_tenant_fr_query_language_en_overlays(self):
        response = self.client.get(
            "/api/v1/products/",
            {"language": "en"},
            HTTP_X_TENANT="tenant-fr-pref",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"][0]["name"], "French name in English row")


class ProductTranslatableAuthoringAPITests(APISetupMixin, APITestCase):
    """PATCH with ``?language=`` creates/updates the French row (I18N-16)."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        self.fr_locale = Locale.objects.get(language_code="fr")
        self.product = create_product(
            sku="AUTH-SKU", name="English only", tenant=self.tenant,
        )

    def test_patch_language_fr_creates_translation_and_get_returns_it(self):
        url = f"/api/v1/products/{self.product.pk}/?language=fr"
        response = self.client.patch(
            url,
            {"name": "Libellé français"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Libellé français")

        fr_row = self.product.get_translation_or_none(self.fr_locale)
        self.assertIsNotNone(fr_row)
        self.assertEqual(fr_row.name, "Libellé français")

        list_en = self.client.get("/api/v1/products/")
        self.assertEqual(list_en.data["results"][0]["name"], "English only")

        list_fr = self.client.get("/api/v1/products/", {"language": "fr"})
        self.assertEqual(list_fr.data["results"][0]["name"], "Libellé français")

    def test_patch_language_fr_updates_existing_translation(self):
        fr_row = self.product.copy_for_translation(self.fr_locale)
        fr_row.name = "Ancien"
        fr_row.save()
        url = f"/api/v1/products/{self.product.pk}/?language=fr"
        response = self.client.patch(
            url,
            {"name": "Mis à jour"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fr_row.refresh_from_db()
        self.assertEqual(fr_row.name, "Mis à jour")
