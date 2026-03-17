from django.test import RequestFactory, TestCase

from tenants.context import get_current_tenant
from tenants.middleware import TenantMiddleware
from tenants.models import TenantRole
from tenants.tests.factories import create_membership, create_tenant, create_user


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
