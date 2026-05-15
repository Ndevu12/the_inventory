"""Platform compliance audit log read-only snippet (cross-tenant, staff/superuser)."""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import NoReverseMatch, reverse
from wagtail.snippets.models import get_snippet_models

from inventory.audit_display import EVENT_SCOPE_PLATFORM
from inventory.models import AuditAction, ComplianceAuditLog
from tests.fixtures.factories import (
    create_platform_staff_user,
    create_platform_superuser,
    create_tenant,
    create_tenant_user,
)

User = get_user_model()


def grant_wagtail_admin_access(user):
    """Wagtail gates /admin/ on ``wagtailadmin.access_admin``, not ``is_staff`` alone."""
    perm = Permission.objects.get(
        content_type__app_label="wagtailadmin",
        codename="access_admin",
    )
    user.user_permissions.add(perm)


class PlatformAuditLogSnippetTests(TestCase):
    def setUp(self):
        super().setUp()
        self.tenant_a = create_tenant(name="Alpha Org", slug="alpha-audit-wagtail")
        self.tenant_b = create_tenant(name="Beta Org", slug="beta-audit-wagtail")
        self.user_a = User.objects.create_user(
            username="audit-wagtail-user-a",
            password="pass12345",
            is_staff=False,
        )
        self.log_a = ComplianceAuditLog.objects.create(
            tenant=self.tenant_a,
            action=AuditAction.PRODUCT_CREATED,
            user=self.user_a,
            details={"sku": "SKU-A"},
        )
        self.log_b = ComplianceAuditLog.objects.create(
            tenant=self.tenant_b,
            action=AuditAction.STOCK_ADJUSTED,
            user=self.user_a,
            details={"sku": "SKU-B"},
        )
        self.log_tenant_accessed = ComplianceAuditLog.objects.create(
            tenant=self.tenant_a,
            action=AuditAction.TENANT_ACCESSED,
            user=self.user_a,
            details={"tenant_slug": "alpha-audit-wagtail", "previous_tenant_slug": "other"},
        )
        self.viewset = ComplianceAuditLog.snippet_viewset
        self.list_url = reverse(self.viewset.get_url_name("list"))
        self.inspect_url_a = reverse(
            self.viewset.get_url_name("inspect"),
            args=[self.log_a.pk],
        )

    def test_registered_as_snippet(self):
        self.assertIn(ComplianceAuditLog, get_snippet_models())

    def test_staff_sees_list_and_both_tenants(self):
        staff = create_platform_staff_user(
            username="wagtail_audit_staff",
            password="staff12345",
        )
        grant_wagtail_admin_access(staff)
        self.client.force_login(staff)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tenant_a.name)
        self.assertContains(response, self.tenant_b.name)
        # Platform-scoped rows (e.g. middleware tenant access) must appear here.
        self.assertContains(response, AuditAction.TENANT_ACCESSED.label)
        self.assertContains(response, EVENT_SCOPE_PLATFORM)

    def test_superuser_sees_list(self):
        su = create_platform_superuser(
            username="wagtail_audit_su",
            password="su12345678",
        )
        self.client.force_login(su)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 200)

    def test_tenant_member_without_admin_perm_redirected(self):
        user = create_tenant_user(self.tenant_a, username="wagtail_audit_member", is_staff=False)
        self.client.force_login(user)
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/admin/login/", response.headers.get("Location", ""))

    def test_staff_without_wagtail_admin_access_forbidden(self):
        """Django ``is_staff`` alone must not open the platform audit snippet."""
        staff = create_platform_staff_user(
            username="wagtail_audit_staff_no_admin_perm",
            password="staff_no_admin_123",
        )
        self.client.force_login(staff)
        response = self.client.get(self.list_url)
        self.assertNotEqual(response.status_code, 200)
        if response.status_code == 302:
            location = response.headers.get("Location", "")
            self.assertIn(
                "/admin/login",
                location,
                msg="staff without ``wagtailadmin.access_admin`` must not reach listing",
            )
        else:
            self.assertEqual(response.status_code, 403)

    def test_staff_can_inspect_not_edit(self):
        staff = create_platform_staff_user(
            username="wagtail_audit_staff2",
            password="staff22345",
        )
        grant_wagtail_admin_access(staff)
        self.client.force_login(staff)
        inspect_resp = self.client.get(self.inspect_url_a)
        self.assertEqual(inspect_resp.status_code, 200)
        base = self.list_url.rstrip("/")
        edit_resp = self.client.get(f"{base}/edit/{self.log_a.pk}/")
        self.assertEqual(edit_resp.status_code, 404)

    def test_read_only_no_add_or_delete_urls(self):
        staff = create_platform_staff_user(
            username="wagtail_audit_staff3",
            password="staff32345",
        )
        grant_wagtail_admin_access(staff)
        self.client.force_login(staff)
        base = self.list_url.rstrip("/")
        add_resp = self.client.get(f"{base}/add/")
        self.assertEqual(add_resp.status_code, 404)
        del_resp = self.client.get(f"{base}/delete/{self.log_a.pk}/")
        self.assertEqual(del_resp.status_code, 404)
        with self.assertRaises(NoReverseMatch):
            reverse(self.viewset.get_url_name("add"))
