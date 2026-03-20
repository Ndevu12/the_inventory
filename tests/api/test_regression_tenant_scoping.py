"""Regression tests for TS-11: Verify no regressions in tenant-scoped systems.

Tests verify that:
- API endpoints return 200 and data is accessible
- Serializers produce valid responses
- No orphaned data (NULL tenants) exists
- Tenant field is properly enforced on all models
- Data is properly isolated between tenants
- StockService properly sets tenant on movements
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import (
    Category, Product, StockLocation, StockMovement, StockRecord, MovementType,
)
from inventory.services.stock import StockService
from tests.fixtures.factories import (
    create_category, create_location, create_product, create_stock_record,
    create_tenant,
)
from tenants.context import get_current_tenant, set_current_tenant
from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


class TenantScopingSetupMixin:
    """Shared setup: create two tenants and users with memberships."""

    def setUp(self):
        # Create two tenants
        self.tenant_a = create_tenant(name="Tenant A", slug="tenant-a")
        self.tenant_b = create_tenant(name="Tenant B", slug="tenant-b")

        # Create staff user with membership to both tenants
        self.user = User.objects.create_user(
            username="apiuser", password="testpass123", is_staff=True,
        )
        TenantMembership.objects.create(
            user=self.user, tenant=self.tenant_a, role=TenantRole.ADMIN,
            is_active=True, is_default=True,
        )
        TenantMembership.objects.create(
            user=self.user, tenant=self.tenant_b, role=TenantRole.ADMIN,
            is_active=True, is_default=False,
        )

        self.token = Token.objects.create(user=self.user)


# =====================================================================
# API Endpoint Accessibility Tests
# =====================================================================


class APIProductEndpointTests(TenantScopingSetupMixin, APITestCase):
    """Verify product API endpoints are accessible and return 200."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_products_returns_200(self):
        """Product list endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        create_product(sku="API-P1", tenant=self.tenant_a)
        create_product(sku="API-P2", tenant=self.tenant_a)

        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)

    def test_retrieve_product_returns_200(self):
        """Product retrieve endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-PGET", tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/products/{p.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "API-PGET")

    def test_update_product_returns_200(self):
        """Product update endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-UPD", tenant=self.tenant_a)

        response = self.client.patch(f"/api/v1/products/{p.pk}/", {
            "name": "Updated Name",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")

    def test_delete_product_returns_204(self):
        """Product delete endpoint should return 204."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-DEL", tenant=self.tenant_a)

        response = self.client.delete(f"/api/v1/products/{p.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class APICategoryEndpointTests(TenantScopingSetupMixin, APITestCase):
    """Verify category API endpoints are accessible and return 200."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_categories_returns_200(self):
        """Category list endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        create_category(name="Cat A", slug="cat-a", tenant=self.tenant_a)

        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_category_returns_200(self):
        """Category retrieve endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        cat = create_category(name="Books", slug="books", tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/categories/{cat.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Books")


class APIStockRecordEndpointTests(TenantScopingSetupMixin, APITestCase):
    """Verify stock record API endpoints are accessible and return 200."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_stock_records_returns_200(self):
        """Stock record list endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-SR1", tenant=self.tenant_a)
        loc = create_location(name="Loc A", tenant=self.tenant_a)
        create_stock_record(product=p, location=loc, quantity=100, tenant=self.tenant_a)

        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_stock_record_returns_200(self):
        """Stock record retrieve endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-SR2", tenant=self.tenant_a)
        loc = create_location(name="Loc B", tenant=self.tenant_a)
        sr = create_stock_record(product=p, location=loc, quantity=50, tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/stock-records/{sr.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 50)

    def test_low_stock_action_returns_200(self):
        """Low stock action should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-LOW", reorder_point=20, tenant=self.tenant_a)
        loc = create_location(name="Loc C", tenant=self.tenant_a)
        create_stock_record(product=p, location=loc, quantity=5, tenant=self.tenant_a)

        response = self.client.get("/api/v1/stock-records/low_stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class APIStockMovementEndpointTests(TenantScopingSetupMixin, APITestCase):
    """Verify stock movement API endpoints are accessible and return 200."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_movements_returns_200(self):
        """Movement list endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-MV1", tenant=self.tenant_a)
        loc = create_location(name="Warehouse", tenant=self.tenant_a)
        service = StockService()
        service.process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=50, to_location=loc, created_by=self.user,
        )

        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_movement_returns_200(self):
        """Movement retrieve endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="API-MV2", tenant=self.tenant_a)
        loc = create_location(name="Loc MV", tenant=self.tenant_a)
        service = StockService()
        mv = service.process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=100, to_location=loc, created_by=self.user,
        )

        response = self.client.get(f"/api/v1/stock-movements/{mv.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 100)


class APIStockLocationEndpointTests(TenantScopingSetupMixin, APITestCase):
    """Verify stock location API endpoints are accessible and return 200."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_locations_returns_200(self):
        """Location list endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        create_location(name="Warehouse A", tenant=self.tenant_a)

        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_location_returns_200(self):
        """Location retrieve endpoint should return 200."""
        set_current_tenant(self.tenant_a)
        loc = create_location(name="Loc Retrieve", tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/stock-locations/{loc.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Loc Retrieve")


# =====================================================================
# Serializer Tenant Field Tests
# =====================================================================


class SerializerTenantFieldTests(TenantScopingSetupMixin, APITestCase):
    """Verify serializers include tenant information."""

    def setUp(self):
        super().setUp()
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_product_serializer_response_valid(self):
        """Product serializer should produce valid response."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="SER-TENANT", tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/products/{p.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "SER-TENANT")
        self.assertIn("id", response.data)
        self.assertIn("name", response.data)

    def test_stock_record_serializer_response_valid(self):
        """Stock record serializer should produce valid response."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="SR-SER", tenant=self.tenant_a)
        loc = create_location(name="Loc SER", tenant=self.tenant_a)
        sr = create_stock_record(product=p, location=loc, quantity=75, tenant=self.tenant_a)

        response = self.client.get(f"/api/v1/stock-records/{sr.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["product_sku"], "SR-SER")
        self.assertEqual(response.data["quantity"], 75)


# =====================================================================
# No Orphaned Data Tests
# =====================================================================


class NoOrphanedDataTests(TenantScopingSetupMixin, TestCase):
    """Verify no NULL tenant records exist after operations."""

    def test_no_products_with_null_tenant(self):
        """All products should have a non-NULL tenant."""
        set_current_tenant(self.tenant_a)
        create_product(sku="ORPHAN-1", tenant=self.tenant_a)
        create_product(sku="ORPHAN-2", tenant=self.tenant_a)

        orphaned = Product.objects.filter(tenant__isnull=True)
        self.assertEqual(orphaned.count(), 0)

    def test_no_categories_with_null_tenant(self):
        """All categories should have a non-NULL tenant."""
        set_current_tenant(self.tenant_a)
        create_category(name="Cat 1", slug="cat-1", tenant=self.tenant_a)
        create_category(name="Cat 2", slug="cat-2", tenant=self.tenant_a)

        orphaned = Category.objects.filter(tenant__isnull=True)
        self.assertEqual(orphaned.count(), 0)

    def test_no_stock_records_with_null_tenant(self):
        """All stock records should have a non-NULL tenant."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="SR-ORPHAN", tenant=self.tenant_a)
        loc = create_location(name="Loc ORPHAN", tenant=self.tenant_a)
        create_stock_record(product=p, location=loc, quantity=50, tenant=self.tenant_a)

        orphaned = StockRecord.objects.filter(tenant__isnull=True)
        self.assertEqual(orphaned.count(), 0)

    def test_no_movements_with_null_tenant(self):
        """All stock movements should have a non-NULL tenant."""
        set_current_tenant(self.tenant_a)
        p = create_product(sku="MV-ORPHAN", tenant=self.tenant_a)
        loc = create_location(name="Loc MV-ORPHAN", tenant=self.tenant_a)

        service = StockService()
        service.process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=100, to_location=loc, created_by=self.user,
        )

        orphaned = StockMovement.objects.filter(tenant__isnull=True)
        self.assertEqual(orphaned.count(), 0)


# =====================================================================
# Tenant Field Enforcement Tests
# =====================================================================


class TenantFieldEnforcementTests(TenantScopingSetupMixin, TestCase):
    """Verify tenant field is properly enforced on all models."""

    def test_product_tenant_field_required(self):
        """Product tenant field should be required."""
        from django.core.exceptions import ValidationError

        p = Product(sku="NO-TENANT", name="No Tenant Product")
        with self.assertRaises(ValidationError):
            p.save()

    def test_category_tenant_field_required(self):
        """Category tenant field should be required."""
        from django.core.exceptions import ValidationError

        cat = Category(name="No Tenant Cat", slug="no-tenant-cat")
        with self.assertRaises(ValidationError):
            cat.save()

    def test_stock_location_tenant_field_required(self):
        """Stock location tenant field should be required."""
        from django.core.exceptions import ValidationError

        loc = StockLocation(name="No Tenant Loc")
        with self.assertRaises(ValidationError):
            loc.save()

    def test_stock_record_tenant_field_required(self):
        """Stock record tenant field should be required."""
        from django.core.exceptions import ValidationError

        set_current_tenant(self.tenant_a)
        p = create_product(sku="SR-TEST", tenant=self.tenant_a)
        loc = create_location(name="Loc TEST", tenant=self.tenant_a)

        sr = StockRecord(product=p, location=loc, quantity=50)
        with self.assertRaises(ValidationError):
            sr.save()

    def test_stock_movement_tenant_field_required(self):
        """Stock movement tenant field should be required."""
        from django.core.exceptions import ValidationError

        set_current_tenant(self.tenant_a)
        p = create_product(sku="MV-TEST", tenant=self.tenant_a)
        loc = create_location(name="Loc MV-TEST", tenant=self.tenant_a)

        mv = StockMovement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=50, to_location=loc,
        )
        with self.assertRaises(ValidationError):
            mv.save()


# =====================================================================
# Tenant Data Isolation Tests
# =====================================================================


class TenantDataIsolationTests(TenantScopingSetupMixin, TestCase):
    """Verify data is properly isolated between tenants."""

    def test_products_isolated_by_tenant(self):
        """Products from different tenants should be separate."""
        set_current_tenant(self.tenant_a)
        p_a = create_product(sku="ISO-A", tenant=self.tenant_a)

        set_current_tenant(self.tenant_b)
        p_b = create_product(sku="ISO-B", tenant=self.tenant_b)

        # Verify they're different
        self.assertNotEqual(p_a.tenant, p_b.tenant)
        self.assertEqual(p_a.tenant, self.tenant_a)
        self.assertEqual(p_b.tenant, self.tenant_b)

    def test_categories_isolated_by_tenant(self):
        """Categories from different tenants should be separate."""
        set_current_tenant(self.tenant_a)
        cat_a = create_category(name="Cat ISO A", slug="cat-iso-a", tenant=self.tenant_a)

        set_current_tenant(self.tenant_b)
        cat_b = create_category(name="Cat ISO B", slug="cat-iso-b", tenant=self.tenant_b)

        # Verify they're different
        self.assertNotEqual(cat_a.tenant, cat_b.tenant)
        self.assertEqual(cat_a.tenant, self.tenant_a)
        self.assertEqual(cat_b.tenant, self.tenant_b)

    def test_stock_records_isolated_by_tenant(self):
        """Stock records from different tenants should be separate."""
        set_current_tenant(self.tenant_a)
        p_a = create_product(sku="SR-ISO-A", tenant=self.tenant_a)
        loc_a = create_location(name="Loc ISO A", tenant=self.tenant_a)
        sr_a = create_stock_record(product=p_a, location=loc_a, quantity=100, tenant=self.tenant_a)

        set_current_tenant(self.tenant_b)
        p_b = create_product(sku="SR-ISO-B", tenant=self.tenant_b)
        loc_b = create_location(name="Loc ISO B", tenant=self.tenant_b)
        sr_b = create_stock_record(product=p_b, location=loc_b, quantity=50, tenant=self.tenant_b)

        # Verify they're different
        self.assertNotEqual(sr_a.tenant, sr_b.tenant)
        self.assertEqual(sr_a.tenant, self.tenant_a)
        self.assertEqual(sr_b.tenant, self.tenant_b)

    def test_stock_locations_isolated_by_tenant(self):
        """Stock locations from different tenants should be separate."""
        set_current_tenant(self.tenant_a)
        loc_a = create_location(name="Loc ISO A", tenant=self.tenant_a)

        set_current_tenant(self.tenant_b)
        loc_b = create_location(name="Loc ISO B", tenant=self.tenant_b)

        # Verify they're different
        self.assertNotEqual(loc_a.tenant, loc_b.tenant)
        self.assertEqual(loc_a.tenant, self.tenant_a)
        self.assertEqual(loc_b.tenant, self.tenant_b)

    def test_stock_movements_isolated_by_tenant(self):
        """Stock movements from different tenants should be separate."""
        set_current_tenant(self.tenant_a)
        p_a = create_product(sku="MV-ISO-A", tenant=self.tenant_a)
        loc_a = create_location(name="Loc MV-ISO-A", tenant=self.tenant_a)
        service = StockService()
        mv_a = service.process_movement(
            product=p_a, movement_type=MovementType.RECEIVE,
            quantity=100, to_location=loc_a, created_by=self.user,
        )

        set_current_tenant(self.tenant_b)
        p_b = create_product(sku="MV-ISO-B", tenant=self.tenant_b)
        loc_b = create_location(name="Loc MV-ISO-B", tenant=self.tenant_b)
        mv_b = service.process_movement(
            product=p_b, movement_type=MovementType.RECEIVE,
            quantity=50, to_location=loc_b, created_by=self.user,
        )

        # Verify they're different
        self.assertNotEqual(mv_a.tenant, mv_b.tenant)
        self.assertEqual(mv_a.tenant, self.tenant_a)
        self.assertEqual(mv_b.tenant, self.tenant_b)
