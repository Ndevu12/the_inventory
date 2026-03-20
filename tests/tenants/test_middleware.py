from django.contrib.sessions.backends.db import SessionStore
from django.test import RequestFactory, TestCase, override_settings

from inventory.models.audit import ComplianceAuditLog
from tenants.context import get_current_tenant
from tenants.middleware import TenantMiddleware
from tenants.models import TenantRole
from tests.fixtures.factories import create_membership, create_tenant, create_user


def _dummy_response(request):
    """Capture tenant from context during request processing."""
    request._captured_tenant = get_current_tenant()
    return "ok"


class TenantMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.mw = TenantMiddleware(_dummy_response)
        self.tenant = create_tenant(slug="acme")
        self.user = create_user()
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_default=True,
        )

    def _make_request(self, user=None, **kwargs):
        request = self.factory.get("/", **kwargs)
        if user:
            request.user = user
        else:
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        return request

    def test_anonymous_gets_no_tenant(self):
        request = self._make_request()
        self.mw(request)
        self.assertIsNone(request.tenant)

    def test_authenticated_gets_default_tenant(self):
        request = self._make_request(user=self.user)
        self.mw(request)
        self.assertEqual(request.tenant, self.tenant)

    def test_header_override(self):
        t2 = create_tenant(slug="beta")
        create_membership(tenant=t2, user=self.user, role=TenantRole.VIEWER)
        request = self._make_request(
            user=self.user,
            HTTP_X_TENANT="beta",
        )
        self.mw(request)
        self.assertEqual(request.tenant, t2)

    def test_header_override_ignores_non_member(self):
        create_tenant(slug="gamma")
        request = self._make_request(
            user=self.user,
            HTTP_X_TENANT="gamma",
        )
        self.mw(request)
        # Falls back to default tenant (user is not a member of gamma)
        self.assertEqual(request.tenant, self.tenant)

    def test_query_param_override(self):
        t2 = create_tenant(slug="delta")
        create_membership(tenant=t2, user=self.user, role=TenantRole.MANAGER)
        request = self.factory.get("/", {"tenant": "delta"})
        request.user = self.user
        self.mw(request)
        self.assertEqual(request.tenant, t2)

    def test_clears_context_after_response(self):
        request = self._make_request(user=self.user)
        self.mw(request)
        self.assertIsNone(get_current_tenant())

    def test_context_set_during_request(self):
        request = self._make_request(user=self.user)
        self.mw(request)
        self.assertEqual(request._captured_tenant, self.tenant)

    def test_inactive_membership_ignored(self):
        user2 = create_user()
        create_membership(
            tenant=self.tenant,
            user=user2,
            role=TenantRole.ADMIN,
            is_active=False,
        )
        request = self._make_request(user=user2)
        self.mw(request)
        self.assertIsNone(request.tenant)

    def test_inactive_tenant_ignored(self):
        t_inactive = create_tenant(is_active=False)
        user2 = create_user()
        create_membership(
            tenant=t_inactive,
            user=user2,
            role=TenantRole.OWNER,
            is_default=True,
        )
        request = self._make_request(user=user2)
        self.mw(request)
        self.assertIsNone(request.tenant)

    def test_fallback_to_first_membership(self):
        user2 = create_user()
        t2 = create_tenant(slug="epsilon")
        create_membership(
            tenant=t2,
            user=user2,
            role=TenantRole.VIEWER,
            is_default=False,
        )
        request = self._make_request(user=user2)
        self.mw(request)
        self.assertEqual(request.tenant, t2)


@override_settings(AUDIT_TENANT_ACCESS=True)
class TenantAccessAuditTest(TestCase):
    """Tests for T-29: Tenant Access Audit Trail."""

    def setUp(self):
        self.factory = RequestFactory()
        self.mw = TenantMiddleware(_dummy_response)
        self.tenant = create_tenant(slug="acme")
        self.tenant2 = create_tenant(slug="beta")
        self.user = create_user()
        create_membership(
            tenant=self.tenant, user=self.user,
            role=TenantRole.ADMIN, is_default=True,
        )
        create_membership(
            tenant=self.tenant2, user=self.user,
            role=TenantRole.VIEWER,
        )

    def _make_request(self, user=None, session=None, **kwargs):
        request = self.factory.get("/", **kwargs)
        if user:
            request.user = user
        else:
            from django.contrib.auth.models import AnonymousUser
            request.user = AnonymousUser()
        request.session = session if session is not None else SessionStore()
        return request

    def test_first_access_creates_audit_log(self):
        request = self._make_request(user=self.user)
        self.mw(request)

        self.assertEqual(ComplianceAuditLog.objects.count(), 1)
        entry = ComplianceAuditLog.objects.first()
        self.assertEqual(entry.action, "tenant_accessed")
        self.assertEqual(entry.tenant, self.tenant)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.details["tenant_slug"], "acme")
        self.assertIsNone(entry.details["previous_tenant_slug"])

    def test_same_tenant_does_not_create_duplicate_log(self):
        session = SessionStore()
        request = self._make_request(user=self.user, session=session)
        self.mw(request)
        self.assertEqual(ComplianceAuditLog.objects.count(), 1)

        request2 = self._make_request(user=self.user, session=session)
        self.mw(request2)
        self.assertEqual(ComplianceAuditLog.objects.count(), 1)

    def test_switching_tenant_creates_audit_log(self):
        session = SessionStore()

        request1 = self._make_request(user=self.user, session=session)
        self.mw(request1)
        self.assertEqual(ComplianceAuditLog.objects.count(), 1)

        request2 = self._make_request(
            user=self.user, session=session, HTTP_X_TENANT="beta",
        )
        self.mw(request2)

        self.assertEqual(ComplianceAuditLog.objects.count(), 2)
        entry = ComplianceAuditLog.objects.first()  # ordered by -timestamp
        self.assertEqual(entry.details["tenant_slug"], "beta")
        self.assertEqual(entry.details["previous_tenant_slug"], "acme")

    def test_anonymous_user_no_audit_log(self):
        request = self._make_request()
        self.mw(request)
        self.assertEqual(ComplianceAuditLog.objects.count(), 0)

    @override_settings(AUDIT_TENANT_ACCESS=False)
    def test_disabled_setting_no_audit_log(self):
        request = self._make_request(user=self.user)
        self.mw(request)
        self.assertEqual(ComplianceAuditLog.objects.count(), 0)

    def test_no_session_no_audit_log(self):
        request = self.factory.get("/")
        request.user = self.user
        self.mw(request)
        self.assertEqual(ComplianceAuditLog.objects.count(), 0)

    def test_audit_log_records_ip_address(self):
        request = self._make_request(
            user=self.user, REMOTE_ADDR="192.168.1.42",
        )
        self.mw(request)

        entry = ComplianceAuditLog.objects.first()
        self.assertEqual(entry.ip_address, "192.168.1.42")

    def test_audit_log_records_forwarded_ip(self):
        request = self._make_request(
            user=self.user,
            HTTP_X_FORWARDED_FOR="10.0.0.1, 172.16.0.1",
        )
        self.mw(request)

        entry = ComplianceAuditLog.objects.first()
        self.assertEqual(entry.ip_address, "10.0.0.1")

    def test_session_tracks_tenant_slug(self):
        session = SessionStore()
        request = self._make_request(user=self.user, session=session)
        self.mw(request)

        self.assertEqual(session.get("_audit_last_tenant_slug"), "acme")
