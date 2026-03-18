"""API tests for variance report and cycle history endpoints."""

from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import (
    CycleStatus,
    InventoryVariance,
    VarianceResolution,
    VarianceType,
)
from inventory.tests.factories import (
    create_cycle_count_line,
    create_inventory_cycle,
    create_location,
    create_product,
)

User = get_user_model()


class VarianceAPISetupMixin:
    """Shared setUp: staff user with auth token and cycles with variances."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="rptuser", password="testpass123", is_staff=True,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.warehouse = create_location(name="Warehouse")
        self.product_a = create_product(
            sku="VAPI-A", name="Widget A", unit_cost=Decimal("10.00"),
        )
        self.product_b = create_product(
            sku="VAPI-B", name="Widget B", unit_cost=Decimal("25.00"),
        )

        self.cycle = create_inventory_cycle(
            name="Q1 Count",
            status=CycleStatus.RECONCILED,
            scheduled_date=date(2026, 1, 15),
        )

        line_a = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product_a,
            location=self.warehouse,
            system_quantity=100,
            counted_quantity=95,
        )
        line_b = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product_b,
            location=self.warehouse,
            system_quantity=50,
            counted_quantity=55,
        )

        now = timezone.now()
        InventoryVariance.objects.create(
            cycle=self.cycle,
            count_line=line_a,
            product=self.product_a,
            location=self.warehouse,
            variance_type=VarianceType.SHORTAGE,
            system_quantity=100,
            physical_quantity=95,
            variance_quantity=-5,
            resolution=VarianceResolution.ACCEPTED,
            resolved_by=self.user,
            resolved_at=now,
        )
        InventoryVariance.objects.create(
            cycle=self.cycle,
            count_line=line_b,
            product=self.product_b,
            location=self.warehouse,
            variance_type=VarianceType.SURPLUS,
            system_quantity=50,
            physical_quantity=55,
            variance_quantity=5,
            resolution=VarianceResolution.INVESTIGATING,
            resolved_by=self.user,
            resolved_at=now,
        )


# =====================================================================
# Variance Report API
# =====================================================================


class VarianceReportAPITests(VarianceAPISetupMixin, APITestCase):
    """Test GET /api/v1/reports/variances/"""

    URL = "/api/v1/reports/variances/"

    def test_list_variances(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertIn("summary", response.data)
        self.assertIn("results", response.data)

    def test_filter_by_cycle_id(self):
        response = self.client.get(self.URL, {"cycle_id": self.cycle.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_product_id(self):
        response = self.client.get(self.URL, {"product_id": self.product_a.pk})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["product_sku"], "VAPI-A")

    def test_filter_by_variance_type(self):
        response = self.client.get(self.URL, {"variance_type": "shortage"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["variance_type"], "shortage")

    def test_summary_in_response(self):
        response = self.client.get(self.URL)
        summary = response.data["summary"]
        self.assertEqual(summary["total_variances"], 2)
        self.assertEqual(summary["net_variance"], 0)

    def test_result_fields(self):
        response = self.client.get(self.URL)
        item = response.data["results"][0]
        expected_fields = {
            "id", "cycle_id", "cycle_name", "product_sku", "product_name",
            "location", "variance_type", "variance_type_display",
            "system_quantity", "physical_quantity", "variance_quantity",
            "resolution", "root_cause", "resolved_by", "resolved_at",
            "created_at",
        }
        self.assertTrue(expected_fields.issubset(set(item.keys())))

    def test_csv_export(self):
        response = self.client.get(self.URL, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("variance_report.csv", response["Content-Disposition"])

    def test_pdf_export(self):
        response = self.client.get(self.URL, {"export": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("variance_report.pdf", response["Content-Disposition"])

    def test_unauthenticated_rejected(self):
        self.client.credentials()
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =====================================================================
# Cycle History API
# =====================================================================


class CycleHistoryAPITests(VarianceAPISetupMixin, APITestCase):
    """Test GET /api/v1/reports/cycle-history/"""

    URL = "/api/v1/reports/cycle-history/"

    def test_list_cycles(self):
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 1)
        self.assertIn("results", response.data)

    def test_cycle_metadata(self):
        response = self.client.get(self.URL)
        cycle_data = next(
            c for c in response.data["results"] if c["id"] == self.cycle.pk
        )
        self.assertEqual(cycle_data["name"], "Q1 Count")
        self.assertEqual(cycle_data["status"], CycleStatus.RECONCILED)

    def test_cycle_variance_stats(self):
        response = self.client.get(self.URL)
        cycle_data = next(
            c for c in response.data["results"] if c["id"] == self.cycle.pk
        )
        self.assertEqual(cycle_data["total_variances"], 2)
        self.assertEqual(cycle_data["shortages"], 1)
        self.assertEqual(cycle_data["surpluses"], 1)

    def test_csv_export(self):
        response = self.client.get(self.URL, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("cycle_history.csv", response["Content-Disposition"])

    def test_pdf_export(self):
        response = self.client.get(self.URL, {"export": "pdf"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn("cycle_history.pdf", response["Content-Disposition"])

    def test_unauthenticated_rejected(self):
        self.client.credentials()
        response = self.client.get(self.URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
