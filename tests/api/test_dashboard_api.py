"""Tests for dashboard API endpoints."""

from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models import ReservationStatus, Warehouse
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_reservation,
    create_stock_lot,
    create_stock_record,
)
from tenants.models import TenantRole
from tests.fixtures.factories import create_membership, create_tenant

User = get_user_model()


class DashboardAPITests(TestCase):
    """Tests for dashboard API endpoints."""

    def setUp(self):
        cache.clear()
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
            "active_warehouses",
            "locations_with_warehouse",
            "locations_retail_site",
            "low_stock_count",
            "total_stock_records",
            "total_reserved",
            "total_available",
            "purchase_orders",
            "sales_orders",
            "reserved_stock_value",
        ]
        for key in expected_keys:
            self.assertIn(key, response.data, f"Missing key: {key}")

    def test_summary_reservation_aware_totals(self):
        product = create_product(tenant=self.tenant)
        location = create_location(tenant=self.tenant)
        create_stock_record(product=product, location=location, quantity=100)
        create_reservation(
            product=product, location=location,
            quantity=30, status=ReservationStatus.PENDING, tenant=self.tenant,
        )
        create_reservation(
            product=product, location=location,
            quantity=20, status=ReservationStatus.CONFIRMED, tenant=self.tenant,
        )
        # Fulfilled reservations should NOT count
        create_reservation(
            product=product, location=location,
            quantity=10, status=ReservationStatus.FULFILLED, tenant=self.tenant,
        )

        url = reverse("api-dashboard-summary")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_reserved"], 50)
        self.assertEqual(response.data["total_available"], 50)

    def test_stock_by_location(self):
        url = reverse("api-stock-by-location")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("labels", response.data)
        self.assertIn("data", response.data)
        self.assertIn("reserved", response.data)
        self.assertIn("available", response.data)

    def test_stock_by_location_reservation_breakdown(self):
        product = create_product(tenant=self.tenant)
        location = create_location(tenant=self.tenant, name="Warehouse A")
        create_stock_record(product=product, location=location, quantity=200)
        create_reservation(
            product=product, location=location,
            quantity=60, status=ReservationStatus.PENDING, tenant=self.tenant,
        )

        url = reverse("api-stock-by-location")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        idx = response.data["labels"].index("Warehouse A")
        self.assertEqual(response.data["data"][idx], 200)
        self.assertEqual(response.data["reserved"][idx], 60)
        self.assertEqual(response.data["available"][idx], 140)

    def test_stock_by_location_by_site_rollup(self):
        product = create_product(tenant=self.tenant, sku="SITE-1")
        wh_a = Warehouse.objects.create(tenant=self.tenant, name="DC Alpha")
        wh_b = Warehouse.objects.create(tenant=self.tenant, name="DC Beta")
        loc_a = create_location(tenant=self.tenant, name="Bin A", warehouse=wh_a)
        loc_b = create_location(tenant=self.tenant, name="Bin B", warehouse=wh_b)
        loc_retail = create_location(tenant=self.tenant, name="Floor", warehouse=None)

        create_stock_record(product=product, location=loc_a, quantity=100)
        create_stock_record(product=product, location=loc_b, quantity=200)
        create_stock_record(product=product, location=loc_retail, quantity=50)
        create_reservation(
            product=product, location=loc_a,
            quantity=25, status=ReservationStatus.CONFIRMED, tenant=self.tenant,
        )

        url = reverse("api-stock-by-location")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("by_site", response.data)
        by_site = response.data["by_site"]
        self.assertEqual(len(by_site), 3)

        def site_row(label):
            matches = [r for r in by_site if r["label"] == label]
            self.assertEqual(len(matches), 1, f"expected one site row for {label!r}")
            return matches[0]

        self.assertEqual(site_row("DC Alpha")["total_quantity"], 100)
        self.assertEqual(site_row("DC Alpha")["reserved"], 25)
        self.assertEqual(site_row("DC Alpha")["available"], 75)
        self.assertEqual(site_row("DC Alpha")["kind"], "warehouse")
        self.assertEqual(site_row("DC Alpha")["warehouse_id"], wh_a.pk)

        self.assertEqual(site_row("DC Beta")["total_quantity"], 200)
        self.assertEqual(site_row("DC Beta")["reserved"], 0)
        self.assertEqual(site_row("DC Beta")["kind"], "warehouse")

        retail = site_row(self.tenant.name)
        self.assertEqual(retail["kind"], "retail_site")
        self.assertIsNone(retail["warehouse_id"])
        self.assertEqual(retail["total_quantity"], 50)

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
        for url_name in [
            "api-dashboard-summary",
            "api-dashboard-reservations",
            "api-dashboard-expiring-lots",
        ]:
            url = reverse(url_name)
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, status.HTTP_401_UNAUTHORIZED,
                f"{url_name} should require authentication",
            )


class PendingReservationsAPITests(TestCase):
    """Tests for the /api/v1/dashboard/reservations/ endpoint."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="reservationuser",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Reservation Corp", slug="reservation-corp")
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_default=True,
        )
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "reservationuser", "password": "testpass123"},
            format="json",
        )
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.product = create_product(
            sku="RES-001", tenant=self.tenant, unit_cost=Decimal("25.00"),
        )
        self.location = create_location(name="Reservation Warehouse", tenant=self.tenant)

    def test_empty_reservations(self):
        url = reverse("api-dashboard-reservations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reservation_count"], 0)
        self.assertEqual(response.data["total_units"], 0)
        self.assertEqual(response.data["total_value"], 0.0)
        self.assertEqual(response.data["pending"], {"count": 0, "units": 0})
        self.assertEqual(response.data["confirmed"], {"count": 0, "units": 0})

    def test_with_active_reservations(self):
        create_stock_record(
            product=self.product, location=self.location, quantity=500,
        )
        create_reservation(
            product=self.product, location=self.location,
            quantity=10, status=ReservationStatus.PENDING, tenant=self.tenant,
        )
        create_reservation(
            product=self.product, location=self.location,
            quantity=20, status=ReservationStatus.CONFIRMED, tenant=self.tenant,
        )
        # Fulfilled should not appear
        create_reservation(
            product=self.product, location=self.location,
            quantity=5, status=ReservationStatus.FULFILLED, tenant=self.tenant,
        )

        url = reverse("api-dashboard-reservations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["reservation_count"], 2)
        self.assertEqual(response.data["total_units"], 30)
        self.assertEqual(response.data["total_value"], 30 * 25.0)
        self.assertEqual(response.data["pending"], {"count": 1, "units": 10})
        self.assertEqual(response.data["confirmed"], {"count": 1, "units": 20})

    def test_response_keys(self):
        url = reverse("api-dashboard-reservations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for key in ["reservation_count", "total_units", "total_value", "pending", "confirmed"]:
            self.assertIn(key, response.data, f"Missing key: {key}")


class ExpiringLotsAPITests(TestCase):
    """Tests for the /api/v1/dashboard/expiring-lots/ endpoint."""

    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="lotuser",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Lot Corp", slug="lot-corp")
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_default=True,
        )
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "lotuser", "password": "testpass123"},
            format="json",
        )
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.product = create_product(sku="LOT-001", tenant=self.tenant)

    def test_no_lot_data_graceful_degradation(self):
        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_lot_data"])
        self.assertEqual(response.data["expiring_lots"], [])

    def test_no_expiring_lots(self):
        create_stock_lot(
            product=self.product,
            lot_number="SAFE-001",
            expiry_date=date.today() + timedelta(days=90),
        )

        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_lot_data"])
        self.assertEqual(response.data["expiring_lots"], [])

    def test_expiring_lots_within_30_days(self):
        expiry_soon = date.today() + timedelta(days=10)
        create_stock_lot(
            product=self.product,
            lot_number="EXPIRE-001",
            expiry_date=expiry_soon,
            quantity_remaining=50,
        )
        # Lot expiring in 60 days should NOT appear
        create_stock_lot(
            product=self.product,
            lot_number="SAFE-002",
            expiry_date=date.today() + timedelta(days=60),
        )

        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_lot_data"])
        self.assertEqual(len(response.data["expiring_lots"]), 1)

        lot_data = response.data["expiring_lots"][0]
        self.assertEqual(lot_data["lot_number"], "EXPIRE-001")
        self.assertEqual(lot_data["product_sku"], "LOT-001")
        self.assertEqual(lot_data["days_to_expiry"], 10)
        self.assertEqual(lot_data["quantity_remaining"], 50)

    def test_already_expired_lot_with_remaining_stock(self):
        """Already-expired lots still show if they have remaining quantity."""
        create_stock_lot(
            product=self.product,
            lot_number="EXPIRED-001",
            expiry_date=date.today() - timedelta(days=5),
            quantity_remaining=25,
        )

        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["expiring_lots"]), 1)
        self.assertTrue(response.data["expiring_lots"][0]["days_to_expiry"] < 0)

    def test_depleted_lot_excluded(self):
        """Lots with zero remaining quantity are excluded."""
        create_stock_lot(
            product=self.product,
            lot_number="EMPTY-001",
            expiry_date=date.today() + timedelta(days=5),
            quantity_remaining=0,
            quantity_received=100,
        )

        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["has_lot_data"])
        self.assertEqual(response.data["expiring_lots"], [])

    def test_response_lot_item_keys(self):
        create_stock_lot(
            product=self.product,
            lot_number="KEY-001",
            expiry_date=date.today() + timedelta(days=15),
            quantity_remaining=10,
        )

        url = reverse("api-dashboard-expiring-lots")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        lot_data = response.data["expiring_lots"][0]
        for key in ["id", "lot_number", "product_sku", "product_name",
                     "expiry_date", "days_to_expiry", "quantity_remaining"]:
            self.assertIn(key, lot_data, f"Missing key: {key}")
