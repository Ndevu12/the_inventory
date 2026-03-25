"""Tests for tenant security in inventory API endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import MovementType, Warehouse
from inventory.services.stock import StockService
from tenants.context import set_current_tenant
from tenants.models import TenantMembership, TenantRole
from tests.fixtures.factories import (
    create_category,
    create_location,
    create_product,
    create_stock_lot,
    create_stock_record,
    create_tenant,
    create_tenant_membership,
    create_user,
)

User = get_user_model()


class TenantSecurityTestCase(APITestCase):
    """Test that users can only access their tenant's data."""

    def setUp(self):
        # Create two tenants
        self.tenant1 = create_tenant(name="Tenant 1", slug="tenant-1")
        self.tenant2 = create_tenant(name="Tenant 2", slug="tenant-2")

        # Create users for each tenant
        self.user1 = create_user(username="user1", is_staff=True)
        self.user2 = create_user(username="user2", is_staff=True)

        # Create memberships
        create_tenant_membership(self.tenant1, self.user1)
        create_tenant_membership(self.tenant2, self.user2)

        # Create tokens
        self.token1 = Token.objects.create(user=self.user1)
        self.token2 = Token.objects.create(user=self.user2)

        # Create data for tenant1
        set_current_tenant(self.tenant1)
        self.cat1 = create_category(name="Category 1", tenant=self.tenant1)
        self.prod1 = create_product(sku="PROD-1", tenant=self.tenant1, category=self.cat1)
        self.loc1 = create_location(name="Location 1", tenant=self.tenant1)
        self.record1 = create_stock_record(self.prod1, self.loc1, quantity=100)
        self.lot1 = create_stock_lot(self.prod1, lot_number="LOT-1")

        # Create data for tenant2
        set_current_tenant(self.tenant2)
        self.cat2 = create_category(name="Category 2", tenant=self.tenant2)
        self.prod2 = create_product(sku="PROD-2", tenant=self.tenant2, category=self.cat2)
        self.loc2 = create_location(name="Location 2", tenant=self.tenant2)
        self.record2 = create_stock_record(self.prod2, self.loc2, quantity=200)
        self.lot2 = create_stock_lot(self.prod2, lot_number="LOT-2")


class CategoryTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for CategoryViewSet."""

    def test_user_can_list_own_tenant_categories(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Category 1")

    def test_user_cannot_see_other_tenant_categories(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [cat["name"] for cat in response.data["results"]]
        self.assertNotIn("Category 2", names)

    def test_user_cannot_retrieve_other_tenant_category(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/categories/{self.cat2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ProductTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for ProductViewSet."""

    def test_user_can_list_own_tenant_products(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "PROD-1")

    def test_user_cannot_see_other_tenant_products(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skus = [prod["sku"] for prod in response.data["results"]]
        self.assertNotIn("PROD-2", skus)

    def test_user_cannot_retrieve_other_tenant_product(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/products/{self.prod2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_use_other_tenant_product_on_custom_actions(self):
        """Custom actions resolve by PK then verify tenant; cross-tenant returns 403."""
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        for path in (
            f"/api/v1/products/{self.prod2.pk}/stock/",
            f"/api/v1/products/{self.prod2.pk}/movements/",
            f"/api/v1/products/{self.prod2.pk}/availability/",
            f"/api/v1/products/{self.prod2.pk}/lots/",
        ):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_product_stock_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/products/{self.prod1.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["quantity"], 100)

    def test_product_movements_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        StockService().process_movement(
            product=self.prod1,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.loc1,
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/products/{self.prod1.pk}/movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_product_lots_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/products/{self.prod1.pk}/lots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["lot_number"], "LOT-1")

    def test_product_availability_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/products/{self.prod1.pk}/availability/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["location"], self.loc1.pk)
        self.assertEqual(response.data[0]["quantity"], 100)

    def test_authenticated_member_without_matching_tenant_context_gets_403(self):
        """Staff user with no tenant membership cannot access inventory APIs."""
        orphan = create_user(username="orphan", is_staff=True)
        orphan_token = Token.objects.create(user=orphan)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {orphan_token.key}")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StockLocationTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for StockLocationViewSet."""

    def test_user_can_list_own_tenant_locations(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Location 1")

    def test_user_cannot_see_other_tenant_locations(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [loc["name"] for loc in response.data["results"]]
        self.assertNotIn("Location 2", names)

    def test_user_cannot_retrieve_other_tenant_location(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-locations/{self.loc2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_use_other_tenant_location_on_stock_action(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-locations/{self.loc2.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_location_stock_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-locations/{self.loc1.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["quantity"], 100)


class WarehouseTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for WarehouseViewSet."""

    def setUp(self):
        super().setUp()
        set_current_tenant(self.tenant1)
        self.wh1 = Warehouse.objects.create(tenant=self.tenant1, name="Warehouse 1")
        set_current_tenant(self.tenant2)
        self.wh2 = Warehouse.objects.create(tenant=self.tenant2, name="Warehouse 2")

    def test_user_can_list_own_tenant_warehouses(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/warehouses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "Warehouse 1")

    def test_user_cannot_see_other_tenant_warehouses(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/warehouses/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [w["name"] for w in response.data["results"]]
        self.assertNotIn("Warehouse 2", names)

    def test_user_cannot_retrieve_other_tenant_warehouse(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/warehouses/{self.wh2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_quick_stats_only_lists_own_tenant_warehouses(self):
        set_current_tenant(self.tenant1)
        loc = create_location(name="T1 bin", tenant=self.tenant1, warehouse=self.wh1)
        p = create_product(sku="WQS-T1", tenant=self.tenant1)
        create_stock_record(product=p, location=loc, quantity=99)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/warehouses/quick-stats/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.wh1.pk)
        self.assertEqual(response.data[0]["total_on_hand"], 99)


class StockRecordTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for StockRecordViewSet."""

    def test_user_can_list_own_tenant_stock_records(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["quantity"], 100)

    def test_user_cannot_see_other_tenant_stock_records(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quantities = [rec["quantity"] for rec in response.data["results"]]
        self.assertNotIn(200, quantities)

    def test_user_cannot_retrieve_other_tenant_stock_record(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-records/{self.record2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_low_stock_action_filters_by_tenant(self):
        set_current_tenant(self.tenant1)
        # Create low stock product
        low_prod = create_product(sku="LOW-1", tenant=self.tenant1, reorder_point=150)
        create_stock_record(low_prod, self.loc1, quantity=50)
        
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-records/low_stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skus = [rec["product_sku"] for rec in response.data]
        self.assertIn("LOW-1", skus)


class StockMovementTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for StockMovementViewSet."""

    def setUp(self):
        super().setUp()
        # Create and update stock movements requires manager (not viewer).
        TenantMembership.objects.filter(
            user=self.user1, tenant=self.tenant1,
        ).update(role=TenantRole.MANAGER)
        # Create movements for each tenant
        set_current_tenant(self.tenant1)
        self.movement1 = StockService().process_movement(
            product=self.prod1,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.loc1,
        )

        set_current_tenant(self.tenant2)
        self.movement2 = StockService().process_movement(
            product=self.prod2,
            movement_type=MovementType.RECEIVE,
            quantity=75,
            to_location=self.loc2,
        )

    def test_user_can_list_own_tenant_movements(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["quantity"], 50)

    def test_user_cannot_see_other_tenant_movements(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quantities = [mov["quantity"] for mov in response.data["results"]]
        self.assertNotIn(75, quantities)

    def test_user_cannot_retrieve_other_tenant_movement(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-movements/{self.movement2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_transfer_rejects_other_tenant_location(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.post("/api/v1/stock-movements/", {
            "product": self.prod1.pk,
            "movement_type": "transfer",
            "quantity": 5,
            "from_location": self.loc1.pk,
            "to_location": self.loc2.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class BulkTransferTenantSecurityTests(TenantSecurityTestCase):
    """Bulk transfer stays within the active tenant's location queryset."""

    URL = "/api/v1/bulk-operations/transfer/"

    def setUp(self):
        super().setUp()
        TenantMembership.objects.filter(
            user=self.user1, tenant=self.tenant1,
        ).update(role=TenantRole.MANAGER)

    def test_bulk_transfer_rejects_other_tenant_to_location_pk(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.post(self.URL, {
            "items": [{"product_id": self.prod1.pk, "quantity": 10}],
            "from_location": self.loc1.pk,
            "to_location": self.loc2.pk,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class StockLotTenantSecurityTests(TenantSecurityTestCase):
    """Test tenant isolation for StockLotViewSet."""

    def test_user_can_list_own_tenant_lots(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-lots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["lot_number"], "LOT-1")

    def test_user_cannot_see_other_tenant_lots(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get("/api/v1/stock-lots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [lot["lot_number"] for lot in response.data["results"]]
        self.assertNotIn("LOT-2", lot_numbers)

    def test_user_cannot_retrieve_other_tenant_lot(self):
        set_current_tenant(self.tenant1)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token1.key}")
        response = self.client.get(f"/api/v1/stock-lots/{self.lot2.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class NoTenantContextTests(APITestCase):
    """Test behavior when no tenant context is available."""

    def setUp(self):
        self.user = create_user(username="notenantuser", is_staff=True)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_no_tenant_context_returns_403(self):
        # Don't set tenant context
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("No tenant context", str(response.data))

    def test_no_tenant_context_on_categories(self):
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_locations(self):
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_warehouses(self):
        response = self.client.get("/api/v1/warehouses/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_warehouses_quick_stats(self):
        response = self.client.get("/api/v1/warehouses/quick-stats/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_stock_records(self):
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_movements(self):
        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_tenant_context_on_lots(self):
        response = self.client.get("/api/v1/stock-lots/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
