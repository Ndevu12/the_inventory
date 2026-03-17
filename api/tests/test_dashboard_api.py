"""Tests for dashboard API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import TenantRole
from tenants.tests.factories import create_membership, create_tenant

User = get_user_model()


class DashboardAPITests(TestCase):
    """Tests for dashboard API endpoints."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="dashboarduser",
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
            {"username": "dashboarduser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

    def test_summary_returns_all_keys(self):
        url = reverse("api-dashboard-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_keys = [
            "total_products",
            "total_locations",
            "low_stock_count",
            "total_stock_records",
            "purchase_orders",
            "sales_orders",
        ]
        for key in expected_keys:
            self.assertIn(key, response.data, f"Missing key: {key}")

    def test_stock_by_location(self):
        url = reverse("api-stock-by-location")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("labels", response.data)
        self.assertIn("data", response.data)

    def test_movement_trends(self):
        url = reverse("api-movement-trends")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("labels", response.data)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["labels"]), 31)
        self.assertEqual(len(response.data["data"]), 31)

    def test_order_status(self):
        url = reverse("api-order-status")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("purchase_orders", response.data)
        self.assertIn("sales_orders", response.data)
        self.assertIn("labels", response.data["purchase_orders"])
        self.assertIn("data", response.data["purchase_orders"])
        self.assertIn("labels", response.data["sales_orders"])
        self.assertIn("data", response.data["sales_orders"])

    def test_unauthenticated(self):
        self.client.credentials()
        url = reverse("api-dashboard-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
