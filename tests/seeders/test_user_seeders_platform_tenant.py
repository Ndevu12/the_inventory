"""WS11: platform operator seeding vs tenant membership seeding."""

from django.contrib.auth import get_user_model
from django.test import TransactionTestCase

from tenants.models import Tenant, TenantMembership, TenantRole
from seeders.seeder_manager import SeederManager

User = get_user_model()


class PlatformTenantUserSeederTestCase(TransactionTestCase):
    """Assert seeded platform accounts have no org memberships; tenant users do.
    
    Cleanup handled by reset_tenant_scoped_models (autouse) fixture.
    """

    def test_full_seed_platform_users_have_no_tenant_membership(self):
        manager = SeederManager(verbose=False, clear_data=False)
        result = manager.seed()
        tenant = result['tenant']
        
        platform_super = User.objects.get(username="platform_super")
        self.assertTrue(platform_super.is_superuser)
        self.assertTrue(platform_super.is_staff)
        self.assertTrue(platform_super.email.endswith("@system.local"))
        self.assertFalse(
            TenantMembership.objects.filter(user=platform_super, tenant=tenant).exists(),
        )

        platform_staff = User.objects.get(username="platform_staff")
        self.assertTrue(platform_staff.is_staff)
        self.assertFalse(platform_staff.is_superuser)
        self.assertTrue(platform_staff.email.endswith("@system.local"))
        self.assertFalse(
            TenantMembership.objects.filter(
                user=platform_staff,
                tenant=tenant,
            ).exists(),
        )

    def test_full_seed_tenant_users_have_memberships_and_no_staff_flag(self):
        manager = SeederManager(verbose=False, clear_data=False)
        result = manager.seed()
        tenant = result['tenant']

        specs = [
            ("owner", TenantRole.OWNER, True),
            ("coordinator", TenantRole.COORDINATOR, False),
            ("manager", TenantRole.MANAGER, False),
            ("tenant_viewer", TenantRole.VIEWER, False),
        ]
        for username, role, is_default in specs:
            with self.subTest(username=username):
                u = User.objects.get(username=username)
                self.assertFalse(u.is_staff)
                self.assertFalse(u.is_superuser)
                m = TenantMembership.objects.get(user=u, tenant=tenant)
                self.assertEqual(m.role, role)
                self.assertEqual(m.is_default, is_default)
                self.assertTrue(
                    u.email.endswith("@org.seed.local"),
                    f"{username} should use tenant seed email domain",
                )

    def test_seed_users_only_accepts_explicit_tenant(self):
        custom = Tenant.objects.create(name="Acme", slug="acme", is_active=True)
        manager = SeederManager(verbose=False, clear_data=False)
        manager.seed_users_only(tenant=custom)

        self.assertTrue(User.objects.filter(username="platform_super").exists())
        owner = User.objects.get(username="owner")
        m = TenantMembership.objects.get(user=owner, tenant=custom)
        self.assertEqual(m.role, TenantRole.OWNER)

