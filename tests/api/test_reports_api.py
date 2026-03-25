"""Tests for report API endpoints."""

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models import ReservationStatus, StockMovementLot
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_reservation,
    create_stock_lot,
    create_stock_movement,
    create_stock_record,
)
from tests.fixtures.factories import create_purchase_order, create_supplier
from tests.fixtures.factories import create_customer, create_sales_order
from tenants.models import TenantRole
from tests.fixtures.factories import create_membership, create_tenant
from tenants.context import set_current_tenant

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
        set_current_tenant(self.tenant)
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
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
        self.client.cookies.clear()
        url = reverse("api-stock-valuation")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # -----------------------------------------------------------------
    # Reservation Summary
    # -----------------------------------------------------------------

    def test_reservation_summary_json(self):
        product = create_product(sku="RSV-001", tenant=self.tenant)
        location = create_location(name="Warehouse RSV", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=100)
        create_reservation(
            product=product, location=location,
            quantity=20, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=product, location=location,
            quantity=10, status=ReservationStatus.CONFIRMED,
        )

        url = reverse("api-reservation-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_status", response.data)
        self.assertEqual(response.data["total_active_reservations"], 2)
        self.assertEqual(response.data["total_reserved_quantity"], 30)

    def test_reservation_summary_csv_export(self):
        url = reverse("api-reservation-summary")
        response = self.client.get(url, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response.get("Content-Type", ""))

    def test_reservation_summary_pdf_export(self):
        url = reverse("api-reservation-summary")
        response = self.client.get(url, {"export": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", response.get("Content-Type", ""))

    # -----------------------------------------------------------------
    # Availability Report
    # -----------------------------------------------------------------

    def test_availability_json(self):
        product = create_product(sku="AVL-001", tenant=self.tenant)
        location = create_location(name="Warehouse AVL", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=100)
        create_reservation(
            product=product, location=location,
            quantity=30, status=ReservationStatus.PENDING,
        )

        url = reverse("api-availability")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertIn("count", response.data)
        self.assertIn("total_reserved_value", response.data)

        item = next(
            r for r in response.data["results"] if r["sku"] == "AVL-001"
        )
        self.assertEqual(item["total_quantity"], 100)
        self.assertEqual(item["reserved_quantity"], 30)
        self.assertEqual(item["available_quantity"], 70)

    def test_availability_filter_by_category(self):
        from tests.fixtures.factories import create_category

        cat = create_category(name="Filtered Cat", slug="filtered-cat")
        product = create_product(
            sku="AVL-CAT", tenant=self.tenant, category=cat,
        )
        location = create_location(name="Warehouse AVLCAT", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=50)

        url = reverse("api-availability")
        response = self.client.get(url, {"category": cat.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        skus = [r["sku"] for r in response.data["results"]]
        self.assertIn("AVL-CAT", skus)

    def test_availability_filter_by_product(self):
        product = create_product(sku="AVL-FLT", tenant=self.tenant)
        location = create_location(name="Warehouse AVLFLT", tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=40)

        url = reverse("api-availability")
        response = self.client.get(url, {"product": product.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["sku"], "AVL-FLT")

    def test_availability_csv_export(self):
        url = reverse("api-availability")
        response = self.client.get(url, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response.get("Content-Type", ""))

    def test_availability_pdf_export(self):
        url = reverse("api-availability")
        response = self.client.get(url, {"export": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", response.get("Content-Type", ""))


class ProductTraceabilityAPITests(TestCase):
    """Tests for the product traceability (GS1) endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="traceuser",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant()
        set_current_tenant(self.tenant)
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_default=True,
        )
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "traceuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.url = reverse("api-product-traceability")

    def _create_lot_with_movements(self):
        """Helper: create a product, lot, and several linked movements."""
        product = create_product(sku="TRACE-001", tenant=self.tenant)
        wh_a = create_location(name="Warehouse A", tenant=self.tenant)
        wh_b = create_location(name="Warehouse B", tenant=self.tenant)

        lot = create_stock_lot(
            product=product,
            lot_number="LOT-2026-A",
            quantity_received=100,
            quantity_remaining=20,
            received_date=date(2026, 1, 15),
            manufacturing_date=date(2025, 12, 1),
            expiry_date=date(2027, 12, 1),
        )

        mv_receive = create_stock_movement(
            product=product,
            movement_type="receive",
            quantity=100,
            to_location=wh_a,
        )
        StockMovementLot.objects.create(
            stock_movement=mv_receive, stock_lot=lot, quantity=100,
        )

        mv_transfer = create_stock_movement(
            product=product,
            movement_type="transfer",
            quantity=50,
            from_location=wh_a,
            to_location=wh_b,
        )
        StockMovementLot.objects.create(
            stock_movement=mv_transfer, stock_lot=lot, quantity=50,
        )

        mv_issue = create_stock_movement(
            product=product,
            movement_type="issue",
            quantity=30,
            from_location=wh_b,
            reference="SO-1234",
        )
        StockMovementLot.objects.create(
            stock_movement=mv_issue, stock_lot=lot, quantity=30,
        )

        return product, lot, [mv_receive, mv_transfer, mv_issue]

    def test_traceability_returns_full_chain(self):
        product, lot, movements = self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.data
        self.assertIn("product", data)
        self.assertIn("lot", data)
        self.assertIn("chain", data)

        self.assertEqual(data["lot"]["lot_number"], "LOT-2026-A")
        self.assertEqual(data["lot"]["manufacturing_date"], "2025-12-01")
        self.assertEqual(data["lot"]["expiry_date"], "2027-12-01")

    def test_chain_ordered_chronologically(self):
        self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        chain = response.data["chain"]
        dates = [entry["date"] for entry in chain]
        self.assertEqual(dates, sorted(dates))

    def test_chain_includes_all_movement_types(self):
        self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        chain = response.data["chain"]
        actions = [entry["action"] for entry in chain]
        self.assertEqual(len(chain), 3)
        self.assertEqual(actions, ["received", "transferred", "issued"])

    def test_receive_entry_has_location(self):
        self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        receive = response.data["chain"][0]
        self.assertEqual(receive["action"], "received")
        self.assertEqual(receive["location"], "Warehouse A")
        self.assertEqual(receive["quantity"], 100)

    def test_transfer_entry_has_from_and_to(self):
        self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        transfer = response.data["chain"][1]
        self.assertEqual(transfer["action"], "transferred")
        self.assertEqual(transfer["from"], "Warehouse A")
        self.assertEqual(transfer["to"], "Warehouse B")
        self.assertEqual(transfer["quantity"], 50)

    def test_issue_entry_has_sales_order(self):
        self._create_lot_with_movements()

        response = self.client.get(self.url, {"product": "TRACE-001", "lot": "LOT-2026-A"})
        issue = response.data["chain"][2]
        self.assertEqual(issue["action"], "issued")
        self.assertEqual(issue["location"], "Warehouse B")
        self.assertEqual(issue["quantity"], 30)
        self.assertEqual(issue["sales_order"], "SO-1234")

    def test_missing_product_param_returns_400(self):
        response = self.client.get(self.url, {"lot": "LOT-001"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_missing_lot_param_returns_400(self):
        response = self.client.get(self.url, {"product": "SKU-001"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nonexistent_product_returns_404(self):
        response = self.client.get(self.url, {"product": "NOPE", "lot": "LOT-X"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_nonexistent_lot_returns_404(self):
        create_product(sku="EXISTS-001", tenant=self.tenant)
        response = self.client.get(self.url, {"product": "EXISTS-001", "lot": "NO-LOT"})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthenticated_returns_401(self):
        self.client.credentials()
        self.client.cookies.clear()
        response = self.client.get(self.url, {"product": "X", "lot": "Y"})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_csv_export(self):
        self._create_lot_with_movements()
        response = self.client.get(
            self.url,
            {"product": "TRACE-001", "lot": "LOT-2026-A", "export": "csv"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("text/csv", response.get("Content-Type", ""))

    def test_pdf_export(self):
        self._create_lot_with_movements()
        response = self.client.get(
            self.url,
            {"product": "TRACE-001", "lot": "LOT-2026-A", "export": "pdf"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", response.get("Content-Type", ""))
