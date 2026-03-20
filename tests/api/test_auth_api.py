"""Comprehensive tests for auth API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import TenantMembership, TenantRole
from tests.fixtures.factories import create_tenant

User = get_user_model()


class AuthLoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )

    def test_login_returns_tokens(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertIn("user", response.data)
        self.assertIsInstance(response.data["user"], dict)

    def test_login_includes_tenant_info(self):
        tenant = create_tenant(name="Acme Corp", slug="acme-corp")
        TenantMembership.objects.create(
            tenant=tenant,
            user=self.user,
            role=TenantRole.ADMIN,
            is_active=True,
            is_default=True,
        )
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tenant", response.data)
        tenant_data = response.data["tenant"]
        self.assertIsNotNone(tenant_data)
        self.assertEqual(tenant_data["id"], tenant.pk)
        self.assertEqual(tenant_data["name"], "Acme Corp")
        self.assertEqual(tenant_data["slug"], "acme-corp")
        self.assertEqual(tenant_data["role"], TenantRole.ADMIN)

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_no_tenant(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tenant", response.data)
        self.assertIsNone(response.data["tenant"])


class AuthRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )

    def test_refresh_returns_new_access_token(self):
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data["refresh"]

        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)


class MeEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            first_name="Test",
            last_name="User",
            is_staff=True,
        )

    def _get_access_token(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        return response.data["access"]

    def test_me_returns_user_profile(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        user_data = response.data["user"]
        self.assertEqual(user_data["username"], "testuser")
        self.assertEqual(user_data["email"], "test@test.com")
        self.assertEqual(user_data["first_name"], "Test")
        self.assertEqual(user_data["last_name"], "User")

    def test_me_unauthenticated(self):
        response = self.client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_patch_updates_profile(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.patch(
            reverse("api-me"),
            {"first_name": "Updated", "email": "updated@test.com"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["first_name"], "Updated")
        self.assertEqual(response.data["email"], "updated@test.com")

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertEqual(self.user.email, "updated@test.com")

    def test_me_includes_memberships(self):
        tenant1 = create_tenant(name="Tenant One", slug="tenant-one")
        tenant2 = create_tenant(name="Tenant Two", slug="tenant-two")
        TenantMembership.objects.create(
            tenant=tenant1,
            user=self.user,
            role=TenantRole.ADMIN,
            is_active=True,
        )
        TenantMembership.objects.create(
            tenant=tenant2,
            user=self.user,
            role=TenantRole.VIEWER,
            is_active=True,
        )

        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("memberships", response.data)
        self.assertEqual(len(response.data["memberships"]), 2)


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )

    def _get_access_token(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        return response.data["access"]

    def test_change_password_success(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            reverse("api-change-password"),
            {"old_password": "testpass123", "new_password": "newpass456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "newpass456"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old(self):
        token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            reverse("api-change-password"),
            {"old_password": "wrongold", "new_password": "newpass456"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
