from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from tenants.models import (
    SubscriptionPlan,
    SubscriptionStatus,
    Tenant,
    TenantInvitation,
    TenantMembership,
    TenantRole,
)
from tests.fixtures.factories import create_membership, create_tenant, create_user


class TenantModelTest(TestCase):
    def test_create_tenant(self):
        t = create_tenant(name="Acme Corp", slug="acme-corp")
        self.assertEqual(str(t), "Acme Corp")
        self.assertTrue(t.is_active)
        self.assertEqual(t.subscription_plan, SubscriptionPlan.FREE)
        self.assertEqual(t.subscription_status, SubscriptionStatus.ACTIVE)
        self.assertEqual(t.preferred_language, "en")

    def test_preferred_language_must_be_supported(self):
        t = create_tenant(name="Lang Co", slug="lang-co")
        t.preferred_language = "xx"
        with self.assertRaises(ValidationError):
            t.full_clean()

    def test_slug_uniqueness(self):
        create_tenant(slug="unique-slug")
        with self.assertRaises(IntegrityError):
            create_tenant(slug="unique-slug")

    def test_display_name_uses_branding(self):
        t = create_tenant(name="Real Name", branding_site_name="Brand Name")
        self.assertEqual(t.display_name, "Brand Name")

    def test_display_name_falls_back_to_name(self):
        t = create_tenant(name="Real Name", branding_site_name="")
        self.assertEqual(t.display_name, "Real Name")

    def test_user_count(self):
        t = create_tenant()
        self.assertEqual(t.user_count(), 0)
        user = create_user()
        create_membership(tenant=t, user=user, role=TenantRole.COORDINATOR)
        self.assertEqual(t.user_count(), 1)

    def test_is_within_user_limit(self):
        t = create_tenant(max_users=1)
        self.assertTrue(t.is_within_user_limit())
        user = create_user()
        create_membership(tenant=t, user=user)
        self.assertFalse(t.is_within_user_limit())

    def test_ordering(self):
        create_tenant(name="Zebra Co")
        create_tenant(name="Alpha Co")
        tenants = list(Tenant.objects.all())
        self.assertEqual(tenants[0].name, "Alpha Co")
        self.assertEqual(tenants[-1].name, "Zebra Co")

    def test_default_subscription_values(self):
        t = Tenant.objects.create(name="Test", slug="test-defaults")
        self.assertEqual(t.max_users, 5)
        self.assertEqual(t.max_products, 100)


class TenantMembershipModelTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()
        self.user = create_user()

    def test_create_membership(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.COORDINATOR)
        self.assertEqual(str(m), f"{self.user} → {self.tenant.name} (Coordinator)")
        self.assertTrue(m.is_active)

    def test_unique_together(self):
        create_membership(tenant=self.tenant, user=self.user)
        # save() runs full_clean(), so duplicate membership raises ValidationError
        # before the database UNIQUE constraint.
        with self.assertRaises(ValidationError):
            create_membership(tenant=self.tenant, user=self.user)

    def test_can_manage_owner(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.OWNER)
        self.assertTrue(m.can_manage)

    def test_can_manage_coordinator(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.COORDINATOR)
        self.assertTrue(m.can_manage)

    def test_can_manage_manager(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.MANAGER)
        self.assertTrue(m.can_manage)

    def test_cannot_manage_viewer(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.VIEWER)
        self.assertFalse(m.can_manage)

    def test_can_manage_organization_owner(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.OWNER)
        self.assertTrue(m.can_manage_organization)

    def test_can_manage_organization_coordinator(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.COORDINATOR)
        self.assertTrue(m.can_manage_organization)

    def test_cannot_manage_organization_manager(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.MANAGER)
        self.assertFalse(m.can_manage_organization)

    def test_is_owner(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.OWNER)
        self.assertTrue(m.is_owner)

    def test_is_not_owner(self):
        m = create_membership(tenant=self.tenant, user=self.user, role=TenantRole.COORDINATOR)
        self.assertFalse(m.is_owner)

    def test_save_rejects_legacy_admin_role(self):
        m = TenantMembership(
            tenant=self.tenant,
            user=self.user,
            role="admin",
            is_active=True,
        )
        with self.assertRaises(ValidationError):
            m.save()

    def test_user_multiple_tenants(self):
        t2 = create_tenant()
        m1 = create_membership(
            tenant=self.tenant, user=self.user, role=TenantRole.OWNER
        )
        m2 = create_membership(
            tenant=t2, user=self.user, role=TenantRole.VIEWER
        )
        memberships = TenantMembership.objects.filter(user=self.user)
        self.assertEqual(memberships.count(), 2)
        self.assertTrue(m1.can_manage)
        self.assertFalse(m2.can_manage)


class TenantInvitationModelTest(TestCase):
    def setUp(self):
        self.tenant = create_tenant()

    def test_save_rejects_legacy_admin_role(self):
        inv = TenantInvitation(
            tenant=self.tenant,
            email="x@example.com",
            role="admin",
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        with self.assertRaises(ValidationError):
            inv.save()
