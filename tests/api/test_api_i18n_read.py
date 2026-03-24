"""Tests for ``?language=`` on translatable API read endpoints (I18N-10, I18N-11)."""

from types import SimpleNamespace

from django.test import RequestFactory, TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase
from wagtail.models import Locale

from api.language import resolve_display_language_code
from api.serializers.inventory import ProductSerializer
from tests.api.test_inventory_api import APISetupMixin
from tests.fixtures.factories import (
    create_customer,
    create_location,
    create_product,
    create_purchase_order,
    create_purchase_order_line,
    create_sales_order,
    create_sales_order_line,
    create_stock_record,
    create_supplier,
    create_tenant,
)


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


class ChoiceLabelLanguageAPITests(APISetupMixin, APITestCase):
    """Choice field ``*_display`` values follow ``?language=`` (I18N-14)."""

    @classmethod
    def setUpTestData(cls):
        Locale.objects.get_or_create(language_code="fr")

    def setUp(self):
        super().setUp()
        self.product = create_product(sku="CHOICE-LBL", tenant=self.tenant)

    def test_product_unit_and_tracking_displays_french(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unit_of_measure"], "pcs")
        self.assertEqual(response.data["unit_of_measure_display"], "Pièces")
        self.assertEqual(response.data["tracking_mode"], "none")
        self.assertEqual(response.data["tracking_mode_display"], "Sans suivi")

    def test_sales_order_status_display_french(self):
        customer = create_customer(
            tenant=self.tenant, code="CHOICE-SO-C", name="Buyer",
        )
        so = create_sales_order(customer=customer, tenant=self.tenant)
        response = self.client.get(
            f"/api/v1/sales-orders/{so.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["status_display"], "Brouillon")

    def test_purchase_order_status_display_french(self):
        supplier = create_supplier(
            tenant=self.tenant, code="CHOICE-PO-S", name="Vendor",
        )
        po = create_purchase_order(supplier=supplier, tenant=self.tenant)
        create_purchase_order_line(po, self.product)
        response = self.client.get(
            f"/api/v1/purchase-orders/{po.pk}/",
            {"language": "fr"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "draft")
        self.assertEqual(response.data["status_display"], "Brouillon")

    def test_reservation_status_display_french(self):
        loc = create_location(name="Choice Loc", tenant=self.tenant)
        create_stock_record(
            product=self.product, location=loc, quantity=50, tenant=self.tenant,
        )
        response = self.client.post(
            "/api/v1/reservations/?language=fr",
            {
                "product": self.product.pk,
                "location": loc.pk,
                "quantity": 5,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "pending")
        self.assertEqual(response.data["status_display"], "En attente")
        rid = response.data["id"]
        response2 = self.client.get(
            f"/api/v1/reservations/{rid}/",
            {"language": "fr"},
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.data["status_display"], "En attente")

    def test_current_tenant_subscription_displays_french(self):
        url = reverse("api-current-tenant")
        response = self.client.get(
            url,
            {"language": "fr"},
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["subscription_plan"], "free")
        self.assertEqual(response.data["subscription_plan_display"], "Gratuit")
        self.assertEqual(response.data["subscription_status"], "active")
        self.assertEqual(response.data["subscription_status_display"], "Actif")

    def test_tenant_member_role_display_french(self):
        url = reverse("api-tenant-members")
        response = self.client.get(
            url,
            {"language": "fr"},
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(
            r for r in response.data["results"]
            if r["username"] == self.user.username
        )
        self.assertEqual(row["role"], "manager")
        self.assertEqual(row["role_display"], "Gestionnaire")
