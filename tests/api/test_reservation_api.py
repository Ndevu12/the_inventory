"""API tests for reservation endpoints."""

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import ReservationStatus
from inventory.services.reservation import ReservationService
from tests.fixtures.factories import (
    create_location,
    create_product,
    create_reservation,
    create_stock_record,
)

User = get_user_model()


class APISetupMixin:
    """Shared setUp: staff user with token + stock fixtures."""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username="manager", password="testpass123", is_staff=True,
        )
        self.staff_token = Token.objects.create(user=self.staff_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.staff_token.key}")

        self.product = create_product(sku="RSV-PROD")
        self.location = create_location(name="Warehouse A")
        create_stock_record(
            product=self.product, location=self.location, quantity=100,
        )

    def _make_viewer_credentials(self):
        """Switch client to a non-staff authenticated user."""
        viewer = User.objects.create_user(
            username="viewer", password="viewpass", is_staff=False,
        )
        token = Token.objects.create(user=viewer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        return viewer


# =====================================================================
# Create Reservation
# =====================================================================


class CreateReservationTests(APISetupMixin, APITestCase):

    def test_create_reservation(self):
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 10,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 10)
        self.assertEqual(response.data["status"], ReservationStatus.PENDING)
        self.assertEqual(response.data["product"], self.product.pk)
        self.assertEqual(response.data["location"], self.location.pk)

    def test_create_reservation_includes_nested_fields(self):
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["product_sku"], "RSV-PROD")
        self.assertEqual(response.data["location_name"], "Warehouse A")
        self.assertEqual(response.data["reserved_by"], self.staff_user.pk)

    def test_create_reservation_with_notes(self):
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 5,
            "notes": "Urgent order",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["notes"], "Urgent order")

    def test_create_reservation_insufficient_stock(self):
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 999,
        })
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_create_reservation_zero_quantity_rejected(self):
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 0,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_reservation_missing_product(self):
        response = self.client.post("/api/v1/reservations/", {
            "location": self.location.pk,
            "quantity": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_viewer_cannot_create_reservation(self):
        self._make_viewer_credentials()
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_create(self):
        self.client.credentials()
        response = self.client.post("/api/v1/reservations/", {
            "product": self.product.pk,
            "location": self.location.pk,
            "quantity": 5,
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =====================================================================
# List / Retrieve Reservations
# =====================================================================


class ListRetrieveReservationTests(APISetupMixin, APITestCase):

    def test_list_reservations(self):
        create_reservation(product=self.product, location=self.location, quantity=5)
        create_reservation(
            product=self.product,
            location=create_location(name="Warehouse B"),
            quantity=3,
        )
        response = self.client.get("/api/v1/reservations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_retrieve_reservation(self):
        res = create_reservation(
            product=self.product, location=self.location, quantity=7,
        )
        response = self.client.get(f"/api/v1/reservations/{res.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["quantity"], 7)
        self.assertEqual(response.data["product_sku"], "RSV-PROD")

    def test_filter_by_status(self):
        create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product,
            location=create_location(name="Loc F"),
            status=ReservationStatus.CANCELLED,
        )
        response = self.client.get("/api/v1/reservations/", {"status": "pending"})
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_product(self):
        other_product = create_product(sku="RSV-OTHER")
        create_reservation(product=self.product, location=self.location)
        create_reservation(
            product=other_product,
            location=create_location(name="Loc G"),
        )
        response = self.client.get(
            "/api/v1/reservations/", {"product": self.product.pk},
        )
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_location(self):
        loc2 = create_location(name="Loc H")
        create_reservation(product=self.product, location=self.location)
        create_reservation(product=self.product, location=loc2)
        response = self.client.get(
            "/api/v1/reservations/", {"location": self.location.pk},
        )
        self.assertEqual(response.data["count"], 1)

    def test_viewer_can_list_reservations(self):
        create_reservation(product=self.product, location=self.location)
        self._make_viewer_credentials()
        response = self.client.get("/api/v1/reservations/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_viewer_can_retrieve_reservation(self):
        res = create_reservation(product=self.product, location=self.location)
        self._make_viewer_credentials()
        response = self.client.get(f"/api/v1/reservations/{res.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthenticated_cannot_list(self):
        self.client.credentials()
        response = self.client.get("/api/v1/reservations/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =====================================================================
# Fulfill Reservation
# =====================================================================


class FulfillReservationTests(APISetupMixin, APITestCase):

    def test_fulfill_reservation(self):
        service = ReservationService()
        reservation = service.create_reservation(
            product=self.product,
            location=self.location,
            quantity=10,
            reserved_by=self.staff_user,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/fulfill/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReservationStatus.FULFILLED)
        self.assertIsNotNone(response.data["fulfilled_movement"])

    def test_fulfill_already_cancelled_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.CANCELLED,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/fulfill/",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_fulfill_already_fulfilled_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.FULFILLED,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/fulfill/",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_viewer_cannot_fulfill(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
        )
        self._make_viewer_credentials()
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/fulfill/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =====================================================================
# Cancel Reservation
# =====================================================================


class CancelReservationTests(APISetupMixin, APITestCase):

    def test_cancel_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.PENDING,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/cancel/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReservationStatus.CANCELLED)

    def test_cancel_confirmed_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.CONFIRMED,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/cancel/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], ReservationStatus.CANCELLED)

    def test_cancel_already_fulfilled_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.FULFILLED,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/cancel/",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_cancel_already_cancelled_reservation(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
            status=ReservationStatus.CANCELLED,
        )
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/cancel/",
        )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)

    def test_viewer_cannot_cancel(self):
        reservation = create_reservation(
            product=self.product, location=self.location,
        )
        self._make_viewer_credentials()
        response = self.client.post(
            f"/api/v1/reservations/{reservation.pk}/cancel/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# =====================================================================
# Product Availability Endpoint
# =====================================================================


class ProductAvailabilityTests(APISetupMixin, APITestCase):

    def test_availability_no_reservations(self):
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/availability/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        entry = response.data[0]
        self.assertEqual(entry["location"], self.location.pk)
        self.assertEqual(entry["quantity"], 100)
        self.assertEqual(entry["reserved"], 0)
        self.assertEqual(entry["available"], 100)

    def test_availability_with_reservations(self):
        create_reservation(
            product=self.product, location=self.location,
            quantity=30, status=ReservationStatus.PENDING,
        )
        create_reservation(
            product=self.product, location=self.location,
            quantity=20, status=ReservationStatus.CONFIRMED,
        )
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/availability/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry = response.data[0]
        self.assertEqual(entry["quantity"], 100)
        self.assertEqual(entry["reserved"], 50)
        self.assertEqual(entry["available"], 50)

    def test_availability_excludes_fulfilled_and_cancelled(self):
        create_reservation(
            product=self.product, location=self.location,
            quantity=10, status=ReservationStatus.FULFILLED,
        )
        create_reservation(
            product=self.product, location=self.location,
            quantity=15, status=ReservationStatus.CANCELLED,
        )
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/availability/",
        )
        entry = response.data[0]
        self.assertEqual(entry["reserved"], 0)
        self.assertEqual(entry["available"], 100)

    def test_availability_multiple_locations(self):
        loc2 = create_location(name="Warehouse B")
        create_stock_record(product=self.product, location=loc2, quantity=50)
        create_reservation(
            product=self.product, location=loc2,
            quantity=10, status=ReservationStatus.PENDING,
        )
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/availability/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        by_location = {e["location"]: e for e in response.data}

        loc1_data = by_location[self.location.pk]
        self.assertEqual(loc1_data["quantity"], 100)
        self.assertEqual(loc1_data["reserved"], 0)
        self.assertEqual(loc1_data["available"], 100)

        loc2_data = by_location[loc2.pk]
        self.assertEqual(loc2_data["quantity"], 50)
        self.assertEqual(loc2_data["reserved"], 10)
        self.assertEqual(loc2_data["available"], 40)

    def test_availability_no_stock_records(self):
        product = create_product(sku="RSV-EMPTY")
        response = self.client.get(
            f"/api/v1/products/{product.pk}/availability/",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_non_staff_cannot_read_availability(self):
        """Product endpoints require staff; availability inherits that."""
        self._make_viewer_credentials()
        response = self.client.get(
            f"/api/v1/products/{self.product.pk}/availability/",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
