"""API tests for inventory endpoints."""

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import (
    AuditAction,
    ComplianceAuditLog,
    MovementType,
    ReservationStatus,
    StockRecord,
    Warehouse,
)
from inventory.services.stock import StockService
from tenants.context import set_current_tenant
from tenants.models import TenantRole
from tests.fixtures.factories import (
    create_category,
    create_child_location,
    create_location,
    create_product,
    create_reservation,
    create_stock_record,
    create_tenant,
    create_tenant_membership,
    create_warehouse,
)

User = get_user_model()


class APISetupMixin:
    """Shared setUp: create a staff user with a token and tenant context."""

    def setUp(self):
        cache.clear()
        self.tenant = create_tenant(name="API Test Tenant")
        self.user = User.objects.create_user(
            username="apiuser", password="testpass123", is_staff=True,
        )
        create_tenant_membership(self.tenant, self.user, role=TenantRole.MANAGER)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        set_current_tenant(self.tenant)


# =====================================================================
# Products
# =====================================================================


class ProductAPITests(APISetupMixin, APITestCase):

    def test_list_products(self):
        create_product(sku="API-P1")
        create_product(sku="API-P2")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_product(self):
        p = create_product(sku="API-PGET")
        response = self.client.get(f"/api/v1/products/{p.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["sku"], "API-PGET")

    def test_create_product(self):
        response = self.client.post("/api/v1/products/", {
            "sku": "API-NEW",
            "name": "New Product",
            "unit_of_measure": "pcs",
            "unit_cost": "12.50",
            "reorder_point": 10,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["sku"], "API-NEW")
        audit = ComplianceAuditLog.objects.filter(
            tenant=self.tenant, action=AuditAction.PRODUCT_CREATED,
        ).last()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.details.get("sku"), "API-NEW")
        self.assertEqual(audit.product_id, response.data["id"])

    def test_update_product(self):
        p = create_product(sku="API-UPD")
        response = self.client.patch(f"/api/v1/products/{p.pk}/", {
            "name": "Updated Name",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Name")

    def test_delete_product(self):
        p = create_product(sku="API-DEL")
        response = self.client.delete(f"/api/v1/products/{p.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_search_products(self):
        create_product(sku="SRCH-001", name="Widget Alpha")
        create_product(sku="SRCH-002", name="Gadget Beta")
        response = self.client.get("/api/v1/products/", {"search": "Widget"})
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_active(self):
        create_product(sku="ACT-1", is_active=True)
        create_product(sku="ACT-2", is_active=False)
        response = self.client.get("/api/v1/products/", {"is_active": "true"})
        self.assertEqual(response.data["count"], 1)

    def test_product_stock_action(self):
        p = create_product(sku="API-PSTOCK")
        loc = create_location(name="Warehouse")
        create_stock_record(product=p, location=loc, quantity=50)
        response = self.client.get(f"/api/v1/products/{p.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["quantity"], 50)

    def test_unauthenticated_request_rejected(self):
        self.client.credentials()
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_non_staff_rejected(self):
        regular = User.objects.create_user(
            username="regular", password="pass", is_staff=False,
        )
        token = Token.objects.create(user=regular)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get("/api/v1/products/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =====================================================================
# Categories
# =====================================================================


class CategoryAPITests(APISetupMixin, APITestCase):

    def test_list_categories(self):
        create_category(name="Electronics", slug="electronics")
        response = self.client.get("/api/v1/categories/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_retrieve_category(self):
        cat = create_category(name="Books", slug="books")
        response = self.client.get(f"/api/v1/categories/{cat.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Books")


# =====================================================================
# Stock Records
# =====================================================================


class StockRecordAPITests(APISetupMixin, APITestCase):

    def test_list_stock_records(self):
        p = create_product(sku="API-SR1")
        loc = create_location(name="Loc A")
        create_stock_record(product=p, location=loc, quantity=100)
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_stock_records_are_read_only(self):
        response = self.client.post("/api/v1/stock-records/", {
            "product": 1, "location": 1, "quantity": 50,
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_low_stock_action(self):
        p = create_product(sku="API-LOW", reorder_point=20)
        loc = create_location(name="Loc B")
        create_stock_record(product=p, location=loc, quantity=5)
        response = self.client.get("/api/v1/stock-records/low_stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)

    def test_stock_record_includes_reservation_fields(self):
        p = create_product(sku="API-SRF")
        loc = create_location(name="Loc SRF")
        create_stock_record(product=p, location=loc, quantity=100)
        create_reservation(
            product=p, location=loc, quantity=30,
            status=ReservationStatus.PENDING,
        )
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = response.data["results"][0]
        self.assertEqual(record["reserved_quantity"], 30)
        self.assertEqual(record["available_quantity"], 70)

    def test_stock_record_no_reservations_available_equals_quantity(self):
        p = create_product(sku="API-SRNR")
        loc = create_location(name="Loc SRNR")
        create_stock_record(product=p, location=loc, quantity=50)
        response = self.client.get("/api/v1/stock-records/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = response.data["results"][0]
        self.assertEqual(record["reserved_quantity"], 0)
        self.assertEqual(record["available_quantity"], 50)

    def test_low_stock_action_considers_reservations(self):
        """A record above reorder_point physically but low after reservations."""
        p = create_product(sku="API-LSR", reorder_point=10)
        loc = create_location(name="Loc LSR")
        create_stock_record(product=p, location=loc, quantity=50)
        create_reservation(product=p, location=loc, quantity=45)
        response = self.client.get("/api/v1/stock-records/low_stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skus = [r["product_sku"] for r in response.data]
        self.assertIn("API-LSR", skus)


# =====================================================================
# Stock Movements
# =====================================================================


class StockMovementAPITests(APISetupMixin, APITestCase):

    def test_create_receive_movement(self):
        p = create_product(sku="API-MV1")
        loc = create_location(name="Receiving")
        response = self.client.post("/api/v1/stock-movements/", {
            "product": p.pk,
            "movement_type": "receive",
            "quantity": 100,
            "to_location": loc.pk,
            "unit_cost": "10.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 100)
        record = StockRecord.objects.get(product=p, location=loc)
        self.assertEqual(record.quantity, 100)

    def test_create_issue_movement_insufficient_stock(self):
        p = create_product(sku="API-MV2")
        loc = create_location(name="Dock")
        response = self.client.post("/api/v1/stock-movements/", {
            "product": p.pk,
            "movement_type": "issue",
            "quantity": 50,
            "from_location": loc.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_list_movements(self):
        p = create_product(sku="API-MV3")
        loc = create_location(name="Warehouse")
        StockService().process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=50, to_location=loc,
        )
        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_movements_cannot_be_updated(self):
        p = create_product(sku="API-MV4")
        loc = create_location(name="Loc MV")
        mv = StockService().process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=10, to_location=loc,
        )
        response = self.client.patch(f"/api/v1/stock-movements/{mv.pk}/", {
            "quantity": 999,
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_movements_cannot_be_deleted(self):
        p = create_product(sku="API-MV5")
        loc = create_location(name="Loc MV2")
        mv = StockService().process_movement(
            product=p, movement_type=MovementType.RECEIVE,
            quantity=10, to_location=loc,
        )
        response = self.client.delete(f"/api/v1/stock-movements/{mv.pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class StockMovementWarehouseScopeAPITests(APISetupMixin, APITestCase):
    """Stock movement API: facility vs retail partitions and cross-facility moves."""

    def test_create_transfer_cross_warehouse_succeeds(self):
        wh_a = Warehouse.objects.create(tenant=self.tenant, name="DC API A")
        wh_b = Warehouse.objects.create(tenant=self.tenant, name="DC API B")
        loc_a = create_location(name="Bin API A", tenant=self.tenant, warehouse=wh_a)
        loc_b = create_location(name="Bin API B", tenant=self.tenant, warehouse=wh_b)
        p = create_product(sku="API-XWH")
        create_stock_record(product=p, location=loc_a, quantity=40)
        response = self.client.post("/api/v1/stock-movements/", {
            "product": p.pk,
            "movement_type": "transfer",
            "quantity": 15,
            "from_location": loc_a.pk,
            "to_location": loc_b.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            StockRecord.objects.get(product=p, location=loc_a).quantity,
            25,
        )
        self.assertEqual(
            StockRecord.objects.get(product=p, location=loc_b).quantity,
            15,
        )

    def test_create_transfer_mixed_retail_and_facility_is_unprocessable(self):
        wh = Warehouse.objects.create(tenant=self.tenant, name="DC API Retail Mix")
        loc_dc = create_location(name="Dock Mix", tenant=self.tenant, warehouse=wh)
        loc_shop = create_location(name="Floor Mix", tenant=self.tenant, warehouse=None)
        p = create_product(sku="API-MIX")
        create_stock_record(product=p, location=loc_dc, quantity=20)
        response = self.client.post("/api/v1/stock-movements/", {
            "product": p.pk,
            "movement_type": "transfer",
            "quantity": 5,
            "from_location": loc_dc.pk,
            "to_location": loc_shop.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_create_transfer_retail_only_succeeds(self):
        loc_from = create_location(name="Back room API", tenant=self.tenant)
        loc_to = create_location(name="Till API", tenant=self.tenant)
        self.assertIsNone(loc_from.warehouse_id)
        self.assertIsNone(loc_to.warehouse_id)
        p = create_product(sku="API-RTL")
        create_stock_record(product=p, location=loc_from, quantity=12)
        response = self.client.post("/api/v1/stock-movements/", {
            "product": p.pk,
            "movement_type": "transfer",
            "quantity": 4,
            "from_location": loc_from.pk,
            "to_location": loc_to.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            StockRecord.objects.get(product=p, location=loc_from).quantity,
            8,
        )
        self.assertEqual(
            StockRecord.objects.get(product=p, location=loc_to).quantity,
            4,
        )


# =====================================================================
# Stock Locations
# =====================================================================


class StockLocationAPITests(APISetupMixin, APITestCase):

    def test_list_locations(self):
        create_location(name="Warehouse A")
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_list_locations_includes_tree_fields(self):
        root = create_location(name="Root A")
        child = create_child_location(root, name="Child B")
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_id = {row["id"]: row for row in response.data["results"]}
        self.assertIsNone(by_id[root.id]["parent_id"])
        self.assertEqual(by_id[child.id]["parent_id"], root.id)
        self.assertGreaterEqual(by_id[child.id]["depth"], 2)
        self.assertTrue(by_id[child.id]["materialized_path"])

    def test_retrieve_location_includes_ancestor_ids(self):
        root = create_location(name="R")
        mid = create_child_location(root, name="M")
        leaf = create_child_location(mid, name="L")
        response = self.client.get(f"/api/v1/stock-locations/{leaf.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["ancestor_ids"], [root.pk, mid.pk])

    def test_list_locations_filter_id_in(self):
        a = create_location(name="Loc A")
        b = create_location(name="Loc B")
        response = self.client.get(
            "/api/v1/stock-locations/",
            {"id__in": f"{a.pk},{b.pk}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data["results"]}
        self.assertEqual(ids, {a.pk, b.pk})

    def test_list_and_retrieve_locations_include_stock_line_count(self):
        loc_empty = create_location(name="Loc Empty")
        loc_stocked = create_location(name="Loc Stocked")
        for i in range(3):
            p = create_product(sku=f"API-SLC-{i}")
            create_stock_record(product=p, location=loc_stocked, quantity=i + 1)
        list_resp = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        by_id = {row["id"]: row for row in list_resp.data["results"]}
        self.assertEqual(by_id[loc_empty.id]["stock_line_count"], 0)
        self.assertEqual(by_id[loc_stocked.id]["stock_line_count"], 3)
        detail = self.client.get(f"/api/v1/stock-locations/{loc_stocked.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_200_OK)
        self.assertEqual(detail.data["stock_line_count"], 3)

    def test_list_locations_can_order_by_stock_line_count(self):
        create_location(name="Loc Order A")
        loc_b = create_location(name="Loc Order B")
        p = create_product(sku="API-SLO-1")
        create_stock_record(product=p, location=loc_b, quantity=5)
        response = self.client.get(
            "/api/v1/stock-locations/",
            {"ordering": "stock_line_count"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        counts = [row["stock_line_count"] for row in response.data["results"]]
        self.assertEqual(counts, sorted(counts))

    def test_location_stock_action(self):
        loc = create_location(name="Loc Stock")
        p = create_product(sku="API-LS1")
        create_stock_record(product=p, location=loc, quantity=75)
        response = self.client.get(f"/api/v1/stock-locations/{loc.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(len(response.data["results"]), 1)

    def test_location_stock_action_paginates_by_page_size(self):
        loc = create_location(name="Loc Stock Page")
        for i in range(3):
            p = create_product(sku=f"API-LSP-{i}")
            create_stock_record(product=p, location=loc, quantity=i + 1)
        url = f"/api/v1/stock-locations/{loc.pk}/stock/"
        r1 = self.client.get(url, {"page_size": "2", "page": "1"})
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        self.assertEqual(r1.data["count"], 3)
        self.assertEqual(len(r1.data["results"]), 2)
        skus_page1 = [row["product_sku"] for row in r1.data["results"]]
        self.assertEqual(skus_page1, ["API-LSP-0", "API-LSP-1"])
        r2 = self.client.get(url, {"page_size": "2", "page": "2"})
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(len(r2.data["results"]), 1)
        self.assertEqual(r2.data["results"][0]["product_sku"], "API-LSP-2")


# =====================================================================
# Warehouse quick stats
# =====================================================================


class WarehouseQuickStatsAPITests(APISetupMixin, APITestCase):
    """GET /api/v1/warehouses/quick-stats/ — per-facility aggregates."""

    URL = "/api/v1/warehouses/quick-stats/"

    def test_quick_stats_returns_list_ordered_by_name(self):
        create_warehouse(name="Zebra DC", tenant=self.tenant)
        create_warehouse(name="Alpha DC", tenant=self.tenant)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        names = [row["name"] for row in response.data]
        self.assertEqual(names, ["Alpha DC", "Zebra DC"])

    def test_quick_stats_aggregates_locations_stock_reserved_utilization_low_stock(self):
        wh_full = create_warehouse(name="WH Full", tenant=self.tenant)
        wh_low = create_warehouse(name="WH Low", tenant=self.tenant)
        create_warehouse(name="WH Empty", tenant=self.tenant)

        loc_a = create_location(
            name="Bin A",
            tenant=self.tenant,
            warehouse=wh_full,
            max_capacity=100,
        )
        loc_b = create_location(
            name="Bin B",
            tenant=self.tenant,
            warehouse=wh_low,
        )
        p_ok = create_product(sku="API-QS-OK", tenant=self.tenant, reorder_point=5)
        p_low = create_product(sku="API-QS-LOW", tenant=self.tenant, reorder_point=20)
        create_stock_record(product=p_ok, location=loc_a, quantity=30)
        create_stock_record(product=p_low, location=loc_b, quantity=8)
        create_reservation(
            product=p_ok,
            location=loc_a,
            quantity=10,
            status=ReservationStatus.CONFIRMED,
        )

        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_name = {row["name"]: row for row in response.data}

        full = by_name["WH Full"]
        self.assertEqual(full["location_count"], 1)
        self.assertEqual(full["total_on_hand"], 30)
        self.assertEqual(full["reserved_quantity"], 10)
        self.assertEqual(full["available_quantity"], 20)
        self.assertEqual(full["capacity_total"], 100)
        self.assertEqual(full["utilization_percent"], 30.0)
        self.assertEqual(full["low_stock_line_count"], 0)

        low = by_name["WH Low"]
        self.assertEqual(low["location_count"], 1)
        self.assertEqual(low["total_on_hand"], 8)
        self.assertEqual(low["reserved_quantity"], 0)
        self.assertEqual(low["available_quantity"], 8)
        self.assertEqual(low["low_stock_line_count"], 1)

        empty = by_name["WH Empty"]
        self.assertEqual(empty["location_count"], 0)
        self.assertEqual(empty["total_on_hand"], 0)
        self.assertIsNone(empty["utilization_percent"])

    def test_quick_stats_low_stock_respects_reservations(self):
        wh = create_warehouse(name="WH Res", tenant=self.tenant)
        loc = create_location(name="Shelf", tenant=self.tenant, warehouse=wh)
        p = create_product(sku="API-QS-RES", tenant=self.tenant, reorder_point=10)
        create_stock_record(product=p, location=loc, quantity=50)
        create_reservation(product=p, location=loc, quantity=45)
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(r for r in response.data if r["id"] == wh.pk)
        self.assertEqual(row["low_stock_line_count"], 1)
