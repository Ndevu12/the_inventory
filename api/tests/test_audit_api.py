"""API tests for the compliance audit log endpoints (T-30)."""

import csv
import io

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.models import AuditAction, ComplianceAuditLog
from inventory.tests.factories import create_product, create_tenant
from tenants.models import TenantRole
from tenants.tests.factories import create_membership

User = get_user_model()

AUDIT_LOG_URL = "/api/v1/audit-log/"


class AuditLogSetupMixin:
    """Shared setUp: tenant, admin user with membership, and auth token."""

    def setUp(self):
        self.tenant = create_tenant(slug="audit-test")
        self.admin_user = User.objects.create_user(
            username="audit_admin", password="testpass123", is_staff=True,
        )
        create_membership(
            tenant=self.tenant, user=self.admin_user,
            role=TenantRole.ADMIN, is_default=True,
        )
        self.token = Token.objects.create(user=self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def _create_log(self, **kwargs):
        defaults = {
            "tenant": self.tenant,
            "action": AuditAction.STOCK_RECEIVED,
            "user": self.admin_user,
            "ip_address": "127.0.0.1",
            "details": {"quantity": 100},
        }
        defaults.update(kwargs)
        return ComplianceAuditLog.objects.create(**defaults)


class AuditLogListTests(AuditLogSetupMixin, APITestCase):

    def test_list_returns_paginated_results(self):
        self._create_log()
        self._create_log(action=AuditAction.STOCK_ISSUED)
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_list_entry_contains_expected_fields(self):
        product = create_product(sku="AUD-001")
        self._create_log(product=product)
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        entry = response.data["results"][0]
        self.assertIn("id", entry)
        self.assertIn("action", entry)
        self.assertIn("action_display", entry)
        self.assertIn("product_sku", entry)
        self.assertIn("product_name", entry)
        self.assertIn("username", entry)
        self.assertIn("timestamp", entry)
        self.assertIn("ip_address", entry)
        self.assertIn("details", entry)
        self.assertEqual(entry["product_sku"], "AUD-001")
        self.assertEqual(entry["username"], "audit_admin")

    def test_retrieve_single_entry(self):
        log = self._create_log()
        response = self.client.get(f"{AUDIT_LOG_URL}{log.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], log.pk)

    def test_list_empty(self):
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)


class AuditLogFilterTests(AuditLogSetupMixin, APITestCase):

    def test_filter_by_action(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.STOCK_ISSUED)
        self._create_log(action=AuditAction.STOCK_ADJUSTED)
        response = self.client.get(AUDIT_LOG_URL, {"action": "stock_issued"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(
            response.data["results"][0]["action"], "stock_issued",
        )

    def test_filter_by_product(self):
        p1 = create_product(sku="AUD-P1")
        p2 = create_product(sku="AUD-P2")
        self._create_log(product=p1)
        self._create_log(product=p2)
        self._create_log(product=p1)
        response = self.client.get(AUDIT_LOG_URL, {"product": p1.pk})
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_user(self):
        other_user = User.objects.create_user(
            username="other", password="pass", is_staff=True,
        )
        self._create_log(user=self.admin_user)
        self._create_log(user=other_user)
        response = self.client.get(AUDIT_LOG_URL, {"user": self.admin_user.pk})
        self.assertEqual(response.data["count"], 1)

    def test_filter_by_date_range(self):
        old = self._create_log()
        old.timestamp = timezone.now() - timezone.timedelta(days=10)
        ComplianceAuditLog.objects.filter(pk=old.pk).update(timestamp=old.timestamp)

        recent = self._create_log()

        date_from = (timezone.now() - timezone.timedelta(days=2)).isoformat()
        response = self.client.get(AUDIT_LOG_URL, {"date_from": date_from})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], recent.pk)

    def test_filter_by_date_to(self):
        old = self._create_log()
        old_ts = timezone.now() - timezone.timedelta(days=10)
        ComplianceAuditLog.objects.filter(pk=old.pk).update(timestamp=old_ts)

        self._create_log()

        date_to = (timezone.now() - timezone.timedelta(days=5)).isoformat()
        response = self.client.get(AUDIT_LOG_URL, {"date_to": date_to})
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], old.pk)

    def test_combined_filters(self):
        p = create_product(sku="AUD-COMBO")
        self._create_log(action=AuditAction.STOCK_RECEIVED, product=p)
        self._create_log(action=AuditAction.STOCK_ISSUED, product=p)
        self._create_log(action=AuditAction.STOCK_RECEIVED, product=None)
        response = self.client.get(AUDIT_LOG_URL, {
            "action": "stock_received",
            "product": p.pk,
        })
        self.assertEqual(response.data["count"], 1)


class AuditLogCSVExportTests(AuditLogSetupMixin, APITestCase):

    def test_csv_export_via_query_param(self):
        product = create_product(sku="CSV-001")
        self._create_log(product=product)
        self._create_log(action=AuditAction.STOCK_ISSUED)
        response = self.client.get(AUDIT_LOG_URL, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")
        self.assertIn("audit_log.csv", response["Content-Disposition"])

        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(rows[0][0], "ID")
        self.assertEqual(len(rows), 3)  # header + 2 data rows

    def test_csv_export_via_dedicated_endpoint(self):
        self._create_log()
        response = self.client.get(f"{AUDIT_LOG_URL}export/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_csv_export_respects_filters(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.STOCK_ISSUED)
        response = self.client.get(AUDIT_LOG_URL, {
            "export": "csv",
            "action": "stock_received",
        })
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(len(rows), 2)  # header + 1 filtered row

    def test_csv_export_empty(self):
        response = self.client.get(AUDIT_LOG_URL, {"export": "csv"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(len(rows), 1)  # header only


class AuditLogPermissionTests(AuditLogSetupMixin, APITestCase):

    def test_unauthenticated_request_rejected(self):
        self.client.credentials()
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_viewer_role_rejected(self):
        viewer = User.objects.create_user(
            username="viewer", password="pass", is_staff=True,
        )
        create_membership(
            tenant=self.tenant, user=viewer,
            role=TenantRole.VIEWER, is_default=True,
        )
        token = Token.objects.create(user=viewer)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_manager_role_rejected(self):
        manager = User.objects.create_user(
            username="manager", password="pass", is_staff=True,
        )
        create_membership(
            tenant=self.tenant, user=manager,
            role=TenantRole.MANAGER, is_default=True,
        )
        token = Token.objects.create(user=manager)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_role_allowed(self):
        self._create_log()
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_owner_role_allowed(self):
        owner = User.objects.create_user(
            username="owner", password="pass", is_staff=True,
        )
        create_membership(
            tenant=self.tenant, user=owner,
            role=TenantRole.OWNER, is_default=True,
        )
        token = Token.objects.create(user=owner)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self._create_log()
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)

    def test_write_operations_not_allowed(self):
        response = self.client.post(AUDIT_LOG_URL, {
            "action": "stock_received",
        })
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_delete_not_allowed(self):
        log = self._create_log()
        response = self.client.delete(f"{AUDIT_LOG_URL}{log.pk}/")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
