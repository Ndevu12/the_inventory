"""API tests for the compliance audit log endpoints (T-30)."""

import csv
import io

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from inventory.audit_display import EVENT_SCOPE_OPERATIONAL, PLATFORM_AUDIT_ACTIONS
from inventory.models import AuditAction, ComplianceAuditLog
from tests.fixtures.factories import (
    create_membership,
    create_platform_staff_user,
    create_platform_superuser,
    create_product,
    create_tenant,
)
from tenants.models import TenantRole

User = get_user_model()

AUDIT_LOG_URL = "/api/v1/audit-log/"
PLATFORM_AUDIT_LOG_URL = "/api/v1/platform/audit-log/"


def _grant_wagtail_admin_access(user):
    perm = Permission.objects.get(
        content_type__app_label="wagtailadmin",
        codename="access_admin",
    )
    user.user_permissions.add(perm)


class AuditLogSetupMixin:
    """Shared setUp: tenant, coordinator member, and auth token."""

    def setUp(self):
        self.tenant = create_tenant(slug="audit-test")
        self.coordinator_user = User.objects.create_user(
            username="audit_coordinator",
            password="testpass123",
            email="coordinator@org.seed.local",
            is_staff=False,
        )
        create_membership(
            tenant=self.tenant, user=self.coordinator_user,
            role=TenantRole.COORDINATOR, is_default=True,
        )
        self.token = Token.objects.create(user=self.coordinator_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def _create_log(self, **kwargs):
        defaults = {
            "tenant": self.tenant,
            "action": AuditAction.STOCK_RECEIVED,
            "user": self.coordinator_user,
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
        product = create_product(sku="AUD-001", tenant=self.tenant)
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
        self.assertIn("event_scope", entry)
        self.assertIn("summary", entry)
        self.assertEqual(entry["event_scope"], EVENT_SCOPE_OPERATIONAL)
        self.assertEqual(entry["product_sku"], "AUD-001")
        self.assertEqual(entry["username"], "audit_coordinator")

    def test_retrieve_single_entry(self):
        log = self._create_log()
        response = self.client.get(f"{AUDIT_LOG_URL}{log.pk}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], log.pk)

    def test_list_empty(self):
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_list_excludes_platform_scoped_actions_by_default(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.IMPERSONATION_STARTED, details={})
        self._create_log(action=AuditAction.TENANT_EXPORT, details={})
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["action"], AuditAction.STOCK_RECEIVED)
        self.assertEqual(response.data["results"][0]["event_scope"], EVENT_SCOPE_OPERATIONAL)

    def test_list_include_platform_events_does_not_widen_results(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.IMPERSONATION_STARTED, details={})
        default = self.client.get(AUDIT_LOG_URL)
        with_flag = self.client.get(
            AUDIT_LOG_URL, {"include_platform_events": "true"},
        )
        self.assertEqual(default.status_code, status.HTTP_200_OK)
        self.assertEqual(with_flag.status_code, status.HTTP_200_OK)
        self.assertEqual(default.data["count"], 1)
        self.assertEqual(with_flag.data["count"], 1)
        self.assertEqual(with_flag.data["results"][0]["action"], AuditAction.STOCK_RECEIVED)
        self.assertEqual(with_flag.data["results"][0]["event_scope"], EVENT_SCOPE_OPERATIONAL)

    def test_list_include_platform_events_never_returns_platform_scoped_rows(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.TENANT_ACCESSED, details={})
        self._create_log(action=AuditAction.IMPERSONATION_STARTED, details={})
        response = self.client.get(AUDIT_LOG_URL, {"include_platform_events": "true"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertTrue(
            all(item["event_scope"] == EVENT_SCOPE_OPERATIONAL for item in response.data["results"]),
        )
        self.assertTrue(
            all(item["action"] not in PLATFORM_AUDIT_ACTIONS for item in response.data["results"]),
        )

    def test_list_include_platform_alias_ignored(self):
        self._create_log(action=AuditAction.TENANT_DEACTIVATED, details={"reason": "test"})
        response = self.client.get(AUDIT_LOG_URL, {"include_platform": "1"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_include_platform_events_does_not_include_other_tenants(self):
        other_tenant = create_tenant(name="Other Org", slug="audit-other-tenant-iso")
        other_user = User.objects.create_user(
            username="audit_other_tenant_coord",
            password="testpass123",
            is_staff=False,
        )
        create_membership(
            tenant=other_tenant,
            user=other_user,
            role=TenantRole.COORDINATOR,
            is_default=True,
        )
        ComplianceAuditLog.objects.create(
            tenant=other_tenant,
            action=AuditAction.IMPERSONATION_STARTED,
            user=other_user,
            details={},
        )
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.IMPERSONATION_STARTED, details={})
        response = self.client.get(
            AUDIT_LOG_URL,
            {"include_platform_events": "true"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        tenant_pks = {r["tenant"] for r in response.data["results"]}
        self.assertEqual(tenant_pks, {self.tenant.pk})
        self.assertEqual(
            response.data["results"][0]["action"], AuditAction.STOCK_RECEIVED,
        )

    def test_retrieve_platform_scoped_entry_not_found_for_tenant_api(self):
        log = self._create_log(action=AuditAction.IMPERSONATION_STARTED, details={})
        response = self.client.get(f"{AUDIT_LOG_URL}{log.pk}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


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
        p1 = create_product(sku="AUD-P1", tenant=self.tenant)
        p2 = create_product(sku="AUD-P2", tenant=self.tenant)
        self._create_log(product=p1)
        self._create_log(product=p2)
        self._create_log(product=p1)
        response = self.client.get(AUDIT_LOG_URL, {"product": p1.pk})
        self.assertEqual(response.data["count"], 2)

    def test_filter_by_user(self):
        other_user = User.objects.create_user(
            username="audit_other", password="pass", is_staff=False,
        )
        self._create_log(user=self.coordinator_user)
        self._create_log(user=other_user)
        response = self.client.get(AUDIT_LOG_URL, {"user": self.coordinator_user.pk})
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
        p = create_product(sku="AUD-COMBO", tenant=self.tenant)
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
        product = create_product(sku="CSV-001", tenant=self.tenant)
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

    def test_csv_export_omits_platform_rows_by_default(self):
        self._create_log(action=AuditAction.STOCK_RECEIVED)
        self._create_log(action=AuditAction.TENANT_EXPORT, details={})
        response = self.client.get(AUDIT_LOG_URL, {"export": "csv"})
        content = response.content.decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        self.assertEqual(len(rows), 2)  # header + operational only

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

    def test_superuser_without_membership_rejected(self):
        su = User.objects.create_superuser(
            username="platform_su",
            email="su@example.com",
            password="pass",
        )
        token = Token.objects.create(user=su)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        self._create_log()
        response = self.client.get(AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_superuser_with_admin_membership_allowed(self):
        su = User.objects.create_superuser(
            username="platform_su_member",
            email="su2@example.com",
            password="pass",
        )
        create_membership(
            tenant=self.tenant, user=su,
            role=TenantRole.COORDINATOR, is_default=True,
        )
        token = Token.objects.create(user=su)
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


class AuditLogTenantIsolationTests(APITestCase):
    """Tenant audit list/detail never leak another tenant when user has multiple memberships."""

    def setUp(self):
        self.tenant_a = create_tenant(name="Iso A", slug="audit-tenant-iso-a")
        self.tenant_b = create_tenant(name="Iso B", slug="audit-tenant-iso-b")
        self.user = User.objects.create_user(
            username="audit_isolation_user",
            password="testpass123",
            is_staff=False,
        )
        create_membership(
            tenant=self.tenant_a,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_default=True,
        )
        create_membership(
            tenant=self.tenant_b,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_default=False,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.log_a = ComplianceAuditLog.objects.create(
            tenant=self.tenant_a,
            action=AuditAction.STOCK_RECEIVED,
            user=self.user,
            details={"n": "a"},
        )
        self.log_b = ComplianceAuditLog.objects.create(
            tenant=self.tenant_b,
            action=AuditAction.STOCK_ISSUED,
            user=self.user,
            details={"n": "b"},
        )

    def test_list_respects_x_tenant_header(self):
        response = self.client.get(
            AUDIT_LOG_URL,
            HTTP_X_TENANT=self.tenant_a.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {r["id"] for r in response.data["results"]}
        self.assertEqual(ids, {self.log_a.pk})

        response_b = self.client.get(
            AUDIT_LOG_URL,
            HTTP_X_TENANT=self.tenant_b.slug,
        )
        self.assertEqual(response_b.status_code, status.HTTP_200_OK)
        ids_b = {r["id"] for r in response_b.data["results"]}
        self.assertEqual(ids_b, {self.log_b.pk})

    def test_list_platform_rows_excluded_still_scoped_to_active_tenant(self):
        ComplianceAuditLog.objects.create(
            tenant=self.tenant_b,
            action=AuditAction.IMPERSONATION_STARTED,
            user=self.user,
            details={},
        )
        ComplianceAuditLog.objects.create(
            tenant=self.tenant_a,
            action=AuditAction.IMPERSONATION_STARTED,
            user=self.user,
            details={},
        )
        response = self.client.get(
            AUDIT_LOG_URL,
            {"include_platform_events": "true"},
            HTTP_X_TENANT=self.tenant_a.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {r["id"] for r in response.data["results"]}
        self.assertEqual(ids, {self.log_a.pk})
        tenant_pks = {r["tenant"] for r in response.data["results"]}
        self.assertEqual(tenant_pks, {self.tenant_a.pk})
        self.assertTrue(
            all(r["event_scope"] == EVENT_SCOPE_OPERATIONAL for r in response.data["results"]),
        )

    def test_retrieve_other_tenant_log_returns_not_found(self):
        response = self.client.get(
            f"{AUDIT_LOG_URL}{self.log_b.pk}/",
            HTTP_X_TENANT=self.tenant_a.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class PlatformAuditLogAPITests(APITestCase):
    """Cross-tenant platform audit API: superuser or Wagtail admin."""

    def setUp(self):
        super().setUp()
        self.tenant_a = create_tenant(name="Plat A", slug="platform-audit-api-a")
        self.tenant_b = create_tenant(name="Plat B", slug="platform-audit-api-b")
        self.coord_user = User.objects.create_user(
            username="platform_audit_coord_api",
            password="testpass123",
            is_staff=False,
        )
        create_membership(
            tenant=self.tenant_a,
            user=self.coord_user,
            role=TenantRole.COORDINATOR,
            is_default=True,
        )
        self.owner_user = User.objects.create_user(
            username="platform_audit_owner_api",
            password="testpass123",
            is_staff=False,
        )
        create_membership(
            tenant=self.tenant_a,
            user=self.owner_user,
            role=TenantRole.OWNER,
            is_default=True,
        )
        self.log_a = ComplianceAuditLog.objects.create(
            tenant=self.tenant_a,
            action=AuditAction.STOCK_RECEIVED,
            user=self.coord_user,
            details={},
        )
        self.log_b = ComplianceAuditLog.objects.create(
            tenant=self.tenant_b,
            action=AuditAction.STOCK_ISSUED,
            user=self.coord_user,
            details={},
        )

    def test_unauthenticated_forbidden(self):
        self.client.credentials()
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_coordinator_forbidden(self):
        token, _ = Token.objects.get_or_create(user=self.coord_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_forbidden(self):
        token, _ = Token.objects.get_or_create(user=self.owner_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_without_wagtail_admin_forbidden(self):
        staff = create_platform_staff_user(
            username="platform_audit_staff_no_wagtail",
            password="staff_no_wagtail123",
        )
        token, _ = Token.objects.get_or_create(user=staff)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wagtail_admin_non_superuser_sees_cross_tenant_rows(self):
        wagtail_admin = create_platform_staff_user(
            username="platform_audit_wagtail_api",
            password="wagtail_api_pass123",
        )
        _grant_wagtail_admin_access(wagtail_admin)
        token, _ = Token.objects.get_or_create(user=wagtail_admin)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)
        ids = {r["id"] for r in response.data["results"]}
        self.assertIn(self.log_a.pk, ids)
        self.assertIn(self.log_b.pk, ids)

    def test_superuser_sees_cross_tenant_rows(self):
        su = create_platform_superuser(
            username="platform_audit_super_api",
            password="super_api_pass123",
        )
        token, _ = Token.objects.get_or_create(user=su)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
        response = self.client.get(PLATFORM_AUDIT_LOG_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 2)
        ids = {r["id"] for r in response.data["results"]}
        self.assertIn(self.log_a.pk, ids)
        self.assertIn(self.log_b.pk, ids)
