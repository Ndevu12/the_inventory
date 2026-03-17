"""Tests for report API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from inventory.tests.factories import (
    create_location,
    create_product,
    create_stock_record,
)
from procurement.tests.factories import create_purchase_order, create_supplier
from sales.tests.factories import create_customer, create_sales_order
from tenants.models import TenantRole
from tenants.tests.factories import create_membership, create_tenant

User = get_user_model()


class ReportsAPITests(TestCase):
    """Tests for report API endpoints (all GET, require authentication)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="reportuser",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant()
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_default=True,
        )
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "reportuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    def test_stock_valuation_json(self):
        product = create_product(sku="TEST-001", tenant=self.tenant)
        location = create_location(name="Warehouse A", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=50)
        url = reverse("api-stock-valuation")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("items", response.data)
        self.assertIn("method", response.data)

    def test_stock_valuation_csv_export(self):
        url = reverse("api-stock-valuation")
        response = self.client.get(url, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response.get("Content-Type", ""))

    def test_stock_valuation_pdf_export(self):
        url = reverse("api-stock-valuation")
        response = self.client.get(url, {"export": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", response.get("Content-Type", ""))

    def test_movement_history_json(self):
        url = reverse("api-movement-history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_low_stock_json(self):
        product = create_product(
            sku="LOW-001",
            tenant=self.tenant,
            reorder_point=10,
        )
        location = create_location(name="Warehouse B", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=2)
        url = reverse("api-low-stock")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", [])
        skus = [r["sku"] for r in results]
        self.assertIn("LOW-001", skus)

    def test_overstock_json(self):
        url = reverse("api-overstock")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

    def test_purchase_summary_json(self):
        supplier = create_supplier(tenant=self.tenant)
        create_purchase_order(supplier=supplier, tenant=self.tenant)
        url = reverse("api-purchase-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("totals", response.data)

    def test_sales_summary_json(self):
        customer = create_customer(tenant=self.tenant)
        create_sales_order(customer=customer, tenant=self.tenant)
        url = reverse("api-sales-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("totals", response.data)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        url = reverse("api-stock-valuation")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
