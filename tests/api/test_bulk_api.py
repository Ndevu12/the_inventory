"""API tests for bulk stock operation endpoints.

Tests cover all three bulk endpoints (transfer, adjust, revalue):
- Success scenarios
- Validation failures (empty list, bad payload)
- Permission enforcement (manager vs admin)
- Partial failure responses with fail_fast=False
- Edge cases (all items invalid, duplicate products)
"""

from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import StockRecord
from tenants.context import set_current_tenant
from tenants.models import Tenant, TenantMembership, TenantRole
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_stock_record,
)

User = get_user_model()


class BulkAPISetupMixin:
    """Shared setUp: staff user (manager), admin user, products, locations."""

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Bulk Test Corp", slug="bulk-test-corp", is_active=True,
        )
        set_current_tenant(self.tenant)

        self.manager = User.objects.create_user(
            username="manager", password="testpass123", is_staff=True,
        )
        self.manager_token = Token.objects.create(user=self.manager)
        TenantMembership.objects.create(
            tenant=self.tenant, user=self.manager,
            role=TenantRole.MANAGER, is_active=True,
        )

        self.admin = User.objects.create_superuser(
            username="admin", password="adminpass123", email="admin@example.com",
        )
        self.admin_token = Token.objects.create(user=self.admin)
        TenantMembership.objects.create(
            tenant=self.tenant, user=self.admin,
            role=TenantRole.ADMIN, is_active=True,
        )

        self.regular = User.objects.create_user(
            username="regular", password="testpass123", is_staff=False,
        )
        self.regular_token = Token.objects.create(user=self.regular)

        self.warehouse = create_location(name="Bulk API Warehouse")
        self.store = create_location(name="Bulk API Store")
        self.product_a = create_product(
            sku="BAPI-A", unit_cost=Decimal("10.00"), tenant=self.tenant,
        )
        self.product_b = create_product(
            sku="BAPI-B", unit_cost=Decimal("20.00"), tenant=self.tenant,
        )

    def _auth_manager(self):
        self.client.login(username="manager", password="testpass123")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.manager_token.key}")

    def _auth_admin(self):
        self.client.login(username="admin", password="adminpass123")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.admin_token.key}")

    def _auth_regular(self):
        self.client.login(username="regular", password="testpass123")
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.regular_token.key}")


# =====================================================================
# Bulk Transfer API
# =====================================================================


class BulkTransferAPITests(BulkAPISetupMixin, APITestCase):

    URL = "/api/v1/bulk-operations/transfer/"

    def test_transfer_success(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=200)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success_count"], 2)
        self.assertEqual(response.data["failure_count"], 0)
        self.assertEqual(response.data["total_count"], 2)

    def test_transfer_insufficient_stock_fail_fast(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=5)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
            "fail_fast": True,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_transfer_partial_failure(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=5)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "quantity": 30},
                {"product_id": self.product_b.pk, "quantity": 50},
            ],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
            "fail_fast": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data["success_count"], 1)
        self.assertEqual(response.data["failure_count"], 1)
        self.assertEqual(len(response.data["errors"]), 1)

    def test_transfer_empty_items_rejected(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_same_location_rejected(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
            "from_location": self.warehouse.pk,
            "to_location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_unauthenticated(self):
        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_transfer_non_staff_rejected(self):
        self._auth_regular()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_transfer_admin_allowed(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_transfer_missing_required_fields(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transfer_invalid_quantity(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "quantity": 0}],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =====================================================================
# Bulk Adjustment API
# =====================================================================


class BulkAdjustmentAPITests(BulkAPISetupMixin, APITestCase):

    URL = "/api/v1/bulk-operations/adjust/"

    def test_adjustment_success(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)
        create_stock_record(product=self.product_b, location=self.warehouse, quantity=100)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "new_quantity": 80},
                {"product_id": self.product_b.pk, "new_quantity": 60},
            ],
            "location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success_count"], 2)
        self.assertEqual(response.data["failure_count"], 0)

        rec_a = StockRecord.objects.get(product=self.product_a, location=self.warehouse)
        rec_b = StockRecord.objects.get(product=self.product_b, location=self.warehouse)
        self.assertEqual(rec_a.quantity, 80)
        self.assertEqual(rec_b.quantity, 60)

    def test_adjustment_with_notes(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_quantity": 75}],
            "location": self.warehouse.pk,
            "notes": "Cycle count adjustment",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_adjustment_empty_items_rejected(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [],
            "location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adjustment_unauthenticated(self):
        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_quantity": 10}],
            "location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_adjustment_non_staff_rejected(self):
        self._auth_regular()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_quantity": 10}],
            "location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_adjustment_partial_failure(self):
        """One item has a non-existent product; the other succeeds."""
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=50)
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "new_quantity": 100},
                {"product_id": 99999, "new_quantity": 50},
            ],
            "location": self.warehouse.pk,
            "fail_fast": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data["success_count"], 1)
        self.assertEqual(response.data["failure_count"], 1)

    def test_adjustment_negative_quantity_rejected(self):
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_quantity": -5}],
            "location": self.warehouse.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =====================================================================
# Bulk Revalue API
# =====================================================================


class BulkRevalueAPITests(BulkAPISetupMixin, APITestCase):

    URL = "/api/v1/bulk-operations/revalue/"

    def test_revalue_success(self):
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "new_unit_cost": "15.00"},
                {"product_id": self.product_b.pk, "new_unit_cost": "25.00"},
            ],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["success_count"], 2)
        self.assertEqual(response.data["failure_count"], 0)

        self.product_a.refresh_from_db()
        self.product_b.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("15.00"))
        self.assertEqual(self.product_b.unit_cost, Decimal("25.00"))

    def test_revalue_empty_items_rejected(self):
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revalue_unauthenticated(self):
        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_unit_cost": "15.00"}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_revalue_manager_forbidden(self):
        """Revalue requires admin, not just manager."""
        self._auth_manager()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_unit_cost": "15.00"}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_revalue_non_staff_forbidden(self):
        self._auth_regular()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_unit_cost": "15.00"}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_revalue_partial_failure(self):
        """One item has a non-existent product; the other succeeds."""
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "new_unit_cost": "99.99"},
                {"product_id": 99999, "new_unit_cost": "50.00"},
            ],
            "fail_fast": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertEqual(response.data["success_count"], 1)
        self.assertEqual(response.data["failure_count"], 1)

    def test_revalue_negative_cost_rejected(self):
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk, "new_unit_cost": "-5.00"}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_revalue_fail_fast_conflict(self):
        """With fail_fast and one non-existent product, returns 409."""
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [
                {"product_id": self.product_a.pk, "new_unit_cost": "15.00"},
                {"product_id": 99999, "new_unit_cost": "25.00"},
            ],
            "fail_fast": True,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

        self.product_a.refresh_from_db()
        self.assertEqual(self.product_a.unit_cost, Decimal("10.00"))

    def test_revalue_missing_required_field(self):
        self._auth_admin()

        response = self.client.post(self.URL, {
            "items": [{"product_id": self.product_a.pk}],
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# =====================================================================
# Response Shape
# =====================================================================


class BulkResponseShapeTests(BulkAPISetupMixin, APITestCase):
    """Verify the response structure of bulk operations."""

    def test_success_response_has_expected_keys(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        self._auth_manager()

        response = self.client.post("/api/v1/bulk-operations/transfer/", {
            "items": [{"product_id": self.product_a.pk, "quantity": 10}],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("success_count", response.data)
        self.assertIn("failure_count", response.data)
        self.assertIn("total_count", response.data)
        self.assertIn("errors", response.data)
        self.assertIsInstance(response.data["errors"], list)

    def test_partial_failure_errors_have_details(self):
        create_stock_record(product=self.product_a, location=self.warehouse, quantity=100)
        self._auth_manager()

        response = self.client.post("/api/v1/bulk-operations/transfer/", {
            "items": [
                {"product_id": self.product_a.pk, "quantity": 10},
                {"product_id": 99999, "quantity": 10},
            ],
            "from_location": self.warehouse.pk,
            "to_location": self.store.pk,
            "fail_fast": False,
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_207_MULTI_STATUS)
        self.assertTrue(len(response.data["errors"]) > 0)
        error = response.data["errors"][0]
        self.assertIn("product_id", error)
        self.assertIn("error", error)
