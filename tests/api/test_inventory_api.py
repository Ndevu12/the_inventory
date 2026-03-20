"""API tests for inventory endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import MovementType, ReservationStatus, StockRecord
from inventory.services.stock import StockService
from tests.fixtures.factories import (
    create_category,
    create_location,
    create_product,
    create_reservation,
    create_stock_record,
)

User = get_user_model()


class APISetupMixin:
    """Shared setUp: create a staff user with a token."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="apiuser", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


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


# =====================================================================
# Stock Locations
# =====================================================================


class StockLocationAPITests(APISetupMixin, APITestCase):

    def test_list_locations(self):
        create_location(name="Warehouse A")
        response = self.client.get("/api/v1/stock-locations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_location_stock_action(self):
        loc = create_location(name="Loc Stock")
        p = create_product(sku="API-LS1")
        create_stock_record(product=p, location=loc, quantity=75)
        response = self.client.get(f"/api/v1/stock-locations/{loc.pk}/stock/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
