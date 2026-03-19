"""Tests for tenant services."""

from django.contrib.auth import get_user_model
from django.test import TestCase

from tenants.models import (
    SubscriptionPlan,
    Tenant,
    TenantInvitation,
    TenantMembership,
    TenantRole,
)
from tenants.services import create_tenant_with_owner

User = get_user_model()


class CreateTenantWithOwnerTests(TestCase):
    """Tests for create_tenant_with_owner service."""

    def test_create_tenant_without_owner(self):
        tenant, invitation = create_tenant_with_owner(
            name="Acme Corp",
            slug="acme-corp",
        )
        self.assertIsInstance(tenant, Tenant)
        self.assertEqual(tenant.name, "Acme Corp")
        self.assertEqual(tenant.slug, "acme-corp")
        self.assertEqual(tenant.subscription_plan, SubscriptionPlan.FREE)
        self.assertIsNone(invitation)
        self.assertEqual(tenant.memberships.count(), 0)

    def test_create_tenant_with_existing_owner(self):
        user = User.objects.create_user(username="alice", email="alice@example.com")
        tenant, invitation = create_tenant_with_owner(
            name="Acme Corp",
            slug="acme-corp",
            owner_user=user,
        )
        self.assertIsInstance(tenant, Tenant)
        self.assertIsNone(invitation)
        membership = TenantMembership.objects.get(tenant=tenant, user=user)
        self.assertEqual(membership.role, TenantRole.OWNER)
        self.assertTrue(membership.is_default)
        self.assertTrue(user.is_staff)

    def test_create_tenant_with_new_owner_password(self):
        tenant, invitation = create_tenant_with_owner(
            name="Acme Corp",
            slug="acme-corp",
            owner_username="bob",
            owner_email="bob@example.com",
            owner_password="secret123",
        )
        self.assertIsInstance(tenant, Tenant)
        self.assertIsNone(invitation)
        user = User.objects.get(username="bob")
        membership = TenantMembership.objects.get(tenant=tenant, user=user)
        self.assertEqual(membership.role, "owner")
        self.assertTrue(membership.is_default)

    def test_create_tenant_with_owner_invitation(self):
        inviter = User.objects.create_user(username="admin", email="admin@example.com")
        tenant, invitation = create_tenant_with_owner(
            name="Acme Corp",
            slug="acme-corp",
            owner_username="charlie",
            owner_email="charlie@example.com",
            send_owner_invitation=True,
            invited_by=inviter,
        )
        self.assertIsInstance(tenant, Tenant)
        self.assertIsInstance(invitation, TenantInvitation)
        self.assertEqual(invitation.email, "charlie@example.com")
        self.assertEqual(invitation.role, "owner")
        self.assertEqual(invitation.tenant, tenant)
        self.assertEqual(invitation.invited_by, inviter)
        self.assertFalse(User.objects.filter(username="charlie").exists())
