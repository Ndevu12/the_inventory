"""Tests for tenant management API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from wagtail.models import Locale

from tenants.models import TenantInvitation, TenantMembership, TenantRole
from tenants.context import set_current_tenant
from tests.fixtures.factories import create_tenant

User = get_user_model()


class CurrentTenantTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Test Org", slug="test-org")
        set_current_tenant(self.tenant)
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_active=True,
            is_default=True,
        )

    def _get_access_token(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        return response.data["access"]

    def test_get_current_tenant(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(
            reverse("api-current-tenant"),
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Test Org")
        self.assertEqual(response.data["slug"], "test-org")
        self.assertEqual(response.data["preferred_language"], "en")

    def test_patch_tenant_as_admin(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-current-tenant"),
            {"branding_site_name": "Custom Site Name"},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["branding_site_name"], "Custom Site Name")

        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.branding_site_name, "Custom Site Name")

    def test_patch_preferred_language_as_admin(self):
        Locale.objects.get_or_create(language_code="fr")

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-current-tenant"),
            {"preferred_language": "fr"},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["preferred_language"], "fr")
        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.preferred_language, "fr")

    def test_patch_tenant_as_manager(self):
        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.user,
        )
        membership.role = TenantRole.MANAGER
        membership.save()

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-current-tenant"),
            {"name": "Updated Org Name"},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Updated Org Name")

    def test_patch_tenant_denied_for_viewer(self):
        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.user,
        )
        membership.role = TenantRole.VIEWER
        membership.save()

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-current-tenant"),
            {"branding_site_name": "Custom Site Name"},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_invitations_allowed_for_viewer(self):
        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.user,
        )
        membership.role = TenantRole.VIEWER
        membership.save()

        TenantInvitation.objects.create(
            tenant=self.tenant,
            email="invitee@example.com",
            role=TenantRole.VIEWER,
            invited_by=self.user,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(
            reverse("api-tenant-invitations"),
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["email"], "invitee@example.com")

    def test_create_invitation_denied_for_viewer(self):
        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.user,
        )
        membership.role = TenantRole.VIEWER
        membership.save()

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            reverse("api-tenant-invitations"),
            {"email": "new@example.com", "role": TenantRole.VIEWER},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated(self):
        response = self.client.get(
            reverse("api-current-tenant"),
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TenantMemberTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = User.objects.create_user(
            username="adminuser",
            password="testpass123",
            email="admin@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Test Org", slug="test-org")
        set_current_tenant(self.tenant)
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.admin_user,
            role=TenantRole.ADMIN,
            is_active=True,
            is_default=True,
        )

    def _get_admin_token(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "adminuser", "password": "testpass123"},
            format="json",
        )
        return response.data["access"]

    def _login_as_viewer(self):
        membership = TenantMembership.objects.get(
            tenant=self.tenant,
            user=self.admin_user,
        )
        membership.role = TenantRole.VIEWER
        membership.save()
        return self._get_admin_token()

    def test_list_members(self):
        member2 = User.objects.create_user(
            username="member2",
            password="testpass123",
            email="member2@test.com",
            is_staff=True,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=member2,
            role=TenantRole.VIEWER,
            is_active=True,
        )

        token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(
            reverse("api-tenant-members"),
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual(len(response.data["results"]), 2)

    def test_update_member_role(self):
        member2 = User.objects.create_user(
            username="member2",
            password="testpass123",
            email="member2@test.com",
            is_staff=True,
        )
        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=member2,
            role=TenantRole.VIEWER,
            is_active=True,
        )

        token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-tenant-member-detail", kwargs={"pk": membership.pk}),
            {"role": TenantRole.MANAGER},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], TenantRole.MANAGER)

        membership.refresh_from_db()
        self.assertEqual(membership.role, TenantRole.MANAGER)

    def test_delete_member(self):
        member2 = User.objects.create_user(
            username="member2",
            password="testpass123",
            email="member2@test.com",
            is_staff=True,
        )
        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=member2,
            role=TenantRole.VIEWER,
            is_active=True,
        )

        token = self._get_admin_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.delete(
            reverse("api-tenant-member-detail", kwargs={"pk": membership.pk}),
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        self.assertFalse(
            TenantMembership.objects.filter(pk=membership.pk).exists(),
        )

    def test_viewer_cannot_modify_members(self):
        member2 = User.objects.create_user(
            username="member2",
            password="testpass123",
            email="member2@test.com",
            is_staff=True,
        )
        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=member2,
            role=TenantRole.VIEWER,
            is_active=True,
        )

        token = self._login_as_viewer()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-tenant-member-detail", kwargs={"pk": membership.pk}),
            {"role": TenantRole.MANAGER},
            format="json",
            HTTP_X_TENANT=self.tenant.slug,
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
