from django.test import RequestFactory, TestCase

from tenants.context import clear_current_tenant, set_current_tenant
from tenants.models import TenantRole
from tenants.permissions import (
    IsTenantAdmin,
    IsTenantManager,
    IsTenantMember,
    IsTenantOwner,
    TenantReadOnlyOrManager,
    can_admin,
    can_manage,
    get_membership,
    has_role,
    is_owner,
)
from tests.fixtures.factories import create_membership, create_tenant, create_user


class UtilityFunctionTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()
        self.user = create_user()

    def tearDown(self):
        clear_current_tenant()

    def test_get_membership_returns_active(self):
        m = create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.ADMIN
        )
        set_current_tenant(self.tenant)
        self.assertEqual(get_membership(self.user), m)

    def test_get_membership_returns_none_for_inactive(self):
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_active=False,
        )
        set_current_tenant(self.tenant)
        self.assertIsNone(get_membership(self.user))

    def test_get_membership_explicit_tenant(self):
        m = create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.VIEWER
        )
        result = get_membership(self.user, tenant=self.tenant)
        self.assertEqual(result, m)

    def test_has_role(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.MANAGER
        )
        set_current_tenant(self.tenant)
        self.assertTrue(has_role(self.user, TenantRole.MANAGER))
        self.assertFalse(has_role(self.user, TenantRole.OWNER))

    def test_can_manage_owner(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.OWNER)
        set_current_tenant(self.tenant)
        self.assertTrue(can_manage(self.user))

    def test_can_manage_viewer(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.VIEWER)
        set_current_tenant(self.tenant)
        self.assertFalse(can_manage(self.user))

    def test_can_admin_admin(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.ADMIN)
        set_current_tenant(self.tenant)
        self.assertTrue(can_admin(self.user))

    def test_can_admin_manager(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.MANAGER)
        set_current_tenant(self.tenant)
        self.assertFalse(can_admin(self.user))

    def test_is_owner_true(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.OWNER)
        set_current_tenant(self.tenant)
        self.assertTrue(is_owner(self.user))

    def test_is_owner_false(self):
        create_membership(tenant=self.tenant, user=self.user, role=TenantRole.ADMIN)
        set_current_tenant(self.tenant)
        self.assertFalse(is_owner(self.user))


class DRFPermissionClassTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.tenant = create_tenant()
        self.user = create_user()

    def tearDown(self):
        clear_current_tenant()

    def _request(self, method="GET"):
        request = getattr(self.factory, method.lower())("/")
        request.user = self.user
        return request

    def test_is_tenant_member_allows_member(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.VIEWER
        )
        set_current_tenant(self.tenant)
        perm = IsTenantMember()
        self.assertTrue(perm.has_permission(self._request(), None))

    def test_is_tenant_member_denies_non_member(self):
        set_current_tenant(self.tenant)
        perm = IsTenantMember()
        self.assertFalse(perm.has_permission(self._request(), None))

    def test_is_tenant_manager_allows_manager(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.MANAGER
        )
        set_current_tenant(self.tenant)
        perm = IsTenantManager()
        self.assertTrue(perm.has_permission(self._request(), None))

    def test_is_tenant_manager_denies_viewer(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.VIEWER
        )
        set_current_tenant(self.tenant)
        perm = IsTenantManager()
        self.assertFalse(perm.has_permission(self._request(), None))

    def test_is_tenant_admin_allows_admin(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.ADMIN
        )
        set_current_tenant(self.tenant)
        perm = IsTenantAdmin()
        self.assertTrue(perm.has_permission(self._request(), None))

    def test_is_tenant_admin_denies_manager(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.MANAGER
        )
        set_current_tenant(self.tenant)
        perm = IsTenantAdmin()
        self.assertFalse(perm.has_permission(self._request(), None))

    def test_is_tenant_owner_allows_owner(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.OWNER
        )
        set_current_tenant(self.tenant)
        perm = IsTenantOwner()
        self.assertTrue(perm.has_permission(self._request(), None))

    def test_is_tenant_owner_denies_admin(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.ADMIN
        )
        set_current_tenant(self.tenant)
        perm = IsTenantOwner()
        self.assertFalse(perm.has_permission(self._request(), None))

    def test_readonly_or_manager_viewer_read(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.VIEWER
        )
        set_current_tenant(self.tenant)
        perm = TenantReadOnlyOrManager()
        self.assertTrue(perm.has_permission(self._request("GET"), None))

    def test_readonly_or_manager_viewer_write(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.VIEWER
        )
        set_current_tenant(self.tenant)
        perm = TenantReadOnlyOrManager()
        self.assertFalse(perm.has_permission(self._request("POST"), None))

    def test_readonly_or_manager_manager_write(self):
        create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.MANAGER
        )
        set_current_tenant(self.tenant)
        perm = TenantReadOnlyOrManager()
        self.assertTrue(perm.has_permission(self._request("POST"), None))

    def test_is_tenant_member_resolves_tenant_without_thread_local(self):
        """JWT: middleware cleared thread-local; membership still resolves from request."""
        clear_current_tenant()
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.VIEWER,
            is_default=True,
        )
        perm = IsTenantMember()
        self.assertTrue(perm.has_permission(self._request(), None))

    def test_is_tenant_admin_resolves_tenant_without_thread_local(self):
        clear_current_tenant()
        create_membership(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_default=True,
        )
        perm = IsTenantAdmin()
        self.assertTrue(perm.has_permission(self._request(), None))
