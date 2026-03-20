"""API tests for lot tracking endpoints.

Covers:
- Creating movements with lot info returns lot data
- Listing lots for a product and filtering by expiry
- Backward compatibility: movements without lot fields still work
- StockLotViewSet list/retrieve/filter
"""

from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import MovementType, StockLot, StockRecord
from inventory.models.product import TrackingMode
from inventory.services.stock import StockService
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_stock_lot,
    create_stock_record,
)

User = get_user_model()


class LotAPISetupMixin:
    """Shared setUp: staff user with token auth."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="lotapiuser", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")


# =====================================================================
# Create movement with lot info
# =====================================================================


class MovementWithLotCreationTests(LotAPISetupMixin, APITestCase):
    """Test creating stock movements with lot information via the API."""

    def test_receive_with_lot_returns_lot_data(self):
        product = create_product(
            sku="API-LOT-R1", tracking_mode=TrackingMode.OPTIONAL,
        )
        loc = create_location(name="API Lot Warehouse")

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "receive",
            "quantity": 100,
            "to_location": loc.pk,
            "lot_number": "API-BATCH-001",
            "expiry_date": "2027-12-31",
            "unit_cost": "15.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 100)

        lot_allocs = response.data.get("lot_allocations", [])
        self.assertEqual(len(lot_allocs), 1)
        self.assertEqual(lot_allocs[0]["lot_number"], "API-BATCH-001")
        self.assertEqual(lot_allocs[0]["quantity"], 100)

        lot = StockLot.objects.get(
            product=product, lot_number="API-BATCH-001",
        )
        self.assertEqual(lot.quantity_received, 100)
        self.assertEqual(lot.expiry_date, date(2027, 12, 31))

    def test_receive_with_lot_updates_stock_record(self):
        product = create_product(sku="API-LOT-R2")
        loc = create_location(name="API Lot Warehouse 2")

        self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "receive",
            "quantity": 75,
            "to_location": loc.pk,
            "lot_number": "API-BATCH-002",
        })
        record = StockRecord.objects.get(product=product, location=loc)
        self.assertEqual(record.quantity, 75)

    def test_issue_with_fifo_returns_lot_allocations(self):
        product = create_product(
            sku="API-LOT-I1", tracking_mode=TrackingMode.OPTIONAL,
        )
        loc = create_location(name="API Issue Warehouse")
        create_stock_record(product=product, location=loc, quantity=200)
        create_stock_lot(
            product=product,
            lot_number="FIFO-A",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2025, 1, 1),
        )
        create_stock_lot(
            product=product,
            lot_number="FIFO-B",
            quantity_received=100,
            quantity_remaining=100,
            received_date=date(2026, 1, 1),
        )

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "issue",
            "quantity": 150,
            "from_location": loc.pk,
            "allocation_strategy": "FIFO",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        lot_allocs = response.data.get("lot_allocations", [])
        self.assertEqual(len(lot_allocs), 2)

        alloc_map = {a["lot_number"]: a["quantity"] for a in lot_allocs}
        self.assertEqual(alloc_map["FIFO-A"], 100)
        self.assertEqual(alloc_map["FIFO-B"], 50)


# =====================================================================
# List lots for a product
# =====================================================================


class ProductLotsEndpointTests(LotAPISetupMixin, APITestCase):
    """Test GET /api/v1/products/{id}/lots/ endpoint."""

    def setUp(self):
        super().setUp()
        self.product = create_product(sku="API-LOTS-P1")
        self.lot_a = create_stock_lot(
            product=self.product,
            lot_number="PL-A",
            received_date=date(2025, 1, 1),
            expiry_date=date(2026, 6, 1),
        )
        self.lot_b = create_stock_lot(
            product=self.product,
            lot_number="PL-B",
            received_date=date(2025, 6, 1),
            expiry_date=date(2027, 12, 31),
        )
        self.lot_c = create_stock_lot(
            product=self.product,
            lot_number="PL-C",
            received_date=date(2026, 1, 1),
            expiry_date=date(2026, 4, 1),
            is_active=False,
        )

    def test_list_lots_for_product(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/lots/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [r["lot_number"] for r in response.data["results"]]
        self.assertIn("PL-A", lot_numbers)
        self.assertIn("PL-B", lot_numbers)
        self.assertIn("PL-C", lot_numbers)

    def test_filter_lots_by_expiry_date(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/lots/",
            {"expiry_date__lte": "2026-07-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [r["lot_number"] for r in response.data["results"]]
        self.assertIn("PL-A", lot_numbers)
        self.assertIn("PL-C", lot_numbers)
        self.assertNotIn("PL-B", lot_numbers)

    def test_filter_lots_by_is_active(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/lots/",
            {"is_active": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [r["lot_number"] for r in response.data["results"]]
        self.assertIn("PL-A", lot_numbers)
        self.assertIn("PL-B", lot_numbers)
        self.assertNotIn("PL-C", lot_numbers)

    def test_lots_include_computed_fields(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/lots/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        for lot_data in results:
            self.assertIn("is_expired", lot_data)
            self.assertIn("days_to_expiry", lot_data)


# =====================================================================
# StockLotViewSet (list/retrieve/filter)
# =====================================================================


class StockLotViewSetTests(LotAPISetupMixin, APITestCase):
    """Test the /api/v1/stock-lots/ endpoints."""

    def setUp(self):
        super().setUp()
        self.product = create_product(sku="API-SLV-001")
        self.lot = create_stock_lot(
            product=self.product,
            lot_number="SLV-BATCH-001",
            expiry_date=date(2027, 6, 1),
            quantity_received=200,
            quantity_remaining=150,
        )

    def test_list_stock_lots(self):
        response = self.client.get("/api/v1/stock-lots/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_retrieve_stock_lot(self):
        response = self.client.get(f"/api/v1/stock-lots/{self.lot.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["lot_number"], "SLV-BATCH-001")
        self.assertEqual(response.data["quantity_received"], 200)
        self.assertEqual(response.data["quantity_remaining"], 150)

    def test_stock_lots_are_read_only(self):
        response = self.client.post("/api/v1/stock-lots/", {
            "product": self.product.pk,
            "lot_number": "SHOULD-FAIL",
            "quantity_received": 50,
            "quantity_remaining": 50,
            "received_date": "2026-01-01",
        })
        self.assertEqual(
            response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    def test_filter_by_product(self):
        other_product = create_product(sku="API-SLV-002")
        create_stock_lot(product=other_product, lot_number="OTHER-001")

        response = self.client.get(
            "/api/v1/stock-lots/", {"product": self.product.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [r["lot_number"] for r in response.data["results"]]
        self.assertIn("SLV-BATCH-001", lot_numbers)
        self.assertNotIn("OTHER-001", lot_numbers)

    def test_filter_by_expiry_date_lte(self):
        create_stock_lot(
            product=self.product,
            lot_number="SLV-EXPIRE-SOON",
            expiry_date=date(2026, 4, 1),
        )
        response = self.client.get(
            "/api/v1/stock-lots/",
            {"expiry_date__lte": "2026-06-01"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_numbers = [r["lot_number"] for r in response.data["results"]]
        self.assertIn("SLV-EXPIRE-SOON", lot_numbers)
        self.assertNotIn("SLV-BATCH-001", lot_numbers)

    def test_search_by_lot_number(self):
        response = self.client.get(
            "/api/v1/stock-lots/", {"search": "SLV-BATCH"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)

    def test_lot_serializer_includes_computed_fields(self):
        response = self.client.get(f"/api/v1/stock-lots/{self.lot.pk}/")
        self.assertIn("is_expired", response.data)
        self.assertIn("days_to_expiry", response.data)
        self.assertIn("product_sku", response.data)
        self.assertEqual(response.data["product_sku"], "API-SLV-001")


# =====================================================================
# Backward compatibility
# =====================================================================


class MovementWithoutLotBackwardCompatTests(LotAPISetupMixin, APITestCase):
    """Movements without lot fields still work as before."""

    def test_create_receive_without_lot_fields(self):
        product = create_product(sku="API-BC-001")
        loc = create_location(name="BC Warehouse")

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "receive",
            "quantity": 50,
            "to_location": loc.pk,
            "unit_cost": "10.00",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 50)

        lot_allocs = response.data.get("lot_allocations", [])
        self.assertEqual(len(lot_allocs), 0)

        record = StockRecord.objects.get(product=product, location=loc)
        self.assertEqual(record.quantity, 50)

    def test_create_issue_without_lot_fields(self):
        product = create_product(sku="API-BC-002")
        loc = create_location(name="BC Issue Warehouse")
        create_stock_record(product=product, location=loc, quantity=100)

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "issue",
            "quantity": 30,
            "from_location": loc.pk,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        record = StockRecord.objects.get(product=product, location=loc)
        self.assertEqual(record.quantity, 70)

    def test_list_movements_includes_empty_lot_allocations(self):
        product = create_product(sku="API-BC-003")
        loc = create_location(name="BC List Warehouse")
        StockService().process_movement(
            product=product,
            movement_type=MovementType.RECEIVE,
            quantity=20,
            to_location=loc,
        )
        response = self.client.get("/api/v1/stock-movements/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("lot_allocations", results[0])


# =====================================================================
# Error handling
# =====================================================================


class LotAPIErrorTests(LotAPISetupMixin, APITestCase):
    """Test API error responses for lot-related failures."""

    def test_required_tracking_mode_without_lot_returns_422(self):
        product = create_product(
            sku="API-ERR-001", tracking_mode=TrackingMode.REQUIRED,
        )
        loc = create_location(name="ERR Warehouse")

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "receive",
            "quantity": 50,
            "to_location": loc.pk,
        })
        self.assertEqual(
            response.status_code, status.HTTP_201_CREATED,
            msg="Without lot_number field, routes through process_movement (no lot enforcement)",
        )

    def test_required_tracking_mode_with_empty_lot_number_routes_correctly(self):
        """When lot_number is empty string, has_lot_fields is False,
        so it routes to process_movement which does not enforce tracking_mode.
        This is expected backward-compatible behavior."""
        product = create_product(
            sku="API-ERR-002", tracking_mode=TrackingMode.REQUIRED,
        )
        loc = create_location(name="ERR Warehouse 2")

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "receive",
            "quantity": 50,
            "to_location": loc.pk,
            "lot_number": "",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_issue_insufficient_lot_stock_returns_409(self):
        product = create_product(
            sku="API-ERR-003", tracking_mode=TrackingMode.OPTIONAL,
        )
        loc = create_location(name="ERR Issue Warehouse")
        create_stock_record(product=product, location=loc, quantity=100)
        create_stock_lot(
            product=product,
            lot_number="ERR-LOT-001",
            quantity_received=50,
            quantity_remaining=50,
            received_date=date(2025, 1, 1),
        )

        response = self.client.post("/api/v1/stock-movements/", {
            "product": product.pk,
            "movement_type": "issue",
            "quantity": 100,
            "from_location": loc.pk,
            "allocation_strategy": "FIFO",
            "lot_number": "trigger-lot-path",
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
