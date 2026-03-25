"""API tests for inventory cycle count viewset (list/retrieve/filters)."""

from datetime import date

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import CycleStatus, Warehouse
from tenants.context import set_current_tenant
from tenants.models import TenantRole
from tests.fixtures.factories import (
    create_inventory_cycle,
    create_location,
    create_product,
    create_tenant,
    create_tenant_membership,
)

User = get_user_model()


class CycleCountsAPISetupMixin:
    def setUp(self):
        self.tenant = create_tenant(name="Cycle API Tenant")
        self.user = User.objects.create_user(
            username="cycleuser", password="testpass123", is_staff=True,
        )
        create_tenant_membership(self.tenant, self.user, role=TenantRole.MANAGER)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        set_current_tenant(self.tenant)

        self.wh_facility = Warehouse.objects.create(tenant=self.tenant, name="DC One")
        self.loc_linked = create_location(name="Aisle A", tenant=self.tenant)
        self.loc_linked.warehouse = self.wh_facility
        self.loc_linked.save(update_fields=["warehouse"])

        self.loc_retail = create_location(name="Shop Floor", tenant=self.tenant)

        self.product = create_product(sku="CYC-1")

        self.cycle_facility = create_inventory_cycle(
            name="DC count",
            status=CycleStatus.IN_PROGRESS,
            scheduled_date=date(2026, 3, 1),
            location=self.loc_linked,
        )
        self.cycle_retail = create_inventory_cycle(
            name="Retail count",
            status=CycleStatus.SCHEDULED,
            scheduled_date=date(2026, 3, 2),
            location=self.loc_retail,
        )

        self.list_url = "/api/v1/cycle-counts/"


class CycleCountsListFilterTests(CycleCountsAPISetupMixin, APITestCase):
    def test_list_includes_warehouse_fields(self):
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        by_id = {row["id"]: row for row in response.data["results"]}
        self.assertEqual(by_id[self.cycle_facility.pk]["warehouse_id"], self.wh_facility.pk)
        self.assertEqual(by_id[self.cycle_facility.pk]["warehouse_name"], "DC One")
        self.assertIsNone(by_id[self.cycle_retail.pk]["warehouse_id"])
        self.assertIsNone(by_id[self.cycle_retail.pk]["warehouse_name"])

    def test_filter_by_location_warehouse(self):
        response = self.client.get(
            self.list_url,
            {"location__warehouse": self.wh_facility.pk},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data["results"]}
        self.assertIn(self.cycle_facility.pk, ids)
        self.assertNotIn(self.cycle_retail.pk, ids)

    def test_filter_retail_partition_by_null_warehouse(self):
        response = self.client.get(self.list_url, {"location__warehouse__isnull": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in response.data["results"]}
        self.assertIn(self.cycle_retail.pk, ids)
        self.assertNotIn(self.cycle_facility.pk, ids)
