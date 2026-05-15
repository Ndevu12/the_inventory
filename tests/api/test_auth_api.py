"""Comprehensive tests for auth API endpoints."""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from inventory.models.audit import AuditAction, ComplianceAuditLog
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
        self.tenant = create_tenant(name="Login Org", slug="login-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
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
        self.assertNotIn("is_staff", response.data["user"])
        self.assertIn("is_superuser", response.data["user"])
        self.assertIs(response.data["user"]["is_superuser"], False)
        self.assertIn("memberships", response.data)
        self.assertEqual(len(response.data["memberships"]), 1)

    def test_login_includes_tenant_info(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("tenant", response.data)
        tenant_data = response.data["tenant"]
        self.assertIsNotNone(tenant_data)
        self.assertEqual(tenant_data["id"], self.tenant.pk)
        self.assertEqual(tenant_data["name"], "Login Org")
        self.assertEqual(tenant_data["slug"], "login-org")
        self.assertEqual(tenant_data["role"], TenantRole.COORDINATOR)
        self.assertEqual(tenant_data["preferred_language"], "en")
        self.assertIn("memberships", response.data)
        self.assertEqual(len(response.data["memberships"]), 1)
        m0 = response.data["memberships"][0]
        self.assertEqual(m0["tenant__id"], self.tenant.pk)
        self.assertEqual(m0["tenant__name"], "Login Org")
        self.assertEqual(m0["tenant__slug"], "login-org")
        self.assertEqual(m0["tenant__preferred_language"], "en")
        self.assertEqual(m0["role"], TenantRole.COORDINATOR)
        self.assertTrue(m0["is_default"])

    def test_login_invalid_credentials(self):
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_rejects_no_membership(self):
        lone = User.objects.create_user(
            username="nomembership",
            password="testpass123",
            email="none@test.com",
            is_staff=True,
        )
        response = self.client.post(
            reverse("api-login"),
            {"username": lone.username, "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "no_tenant_membership")
        self.assertIn("message", response.data)

    def test_login_succeeds_for_member_who_is_also_superuser(self):
        """Tenant JWT is membership-gated, not denied because of platform flags (WS12)."""
        dual = User.objects.create_user(
            username="dual_console",
            password="testpass123",
            email="dual@test.com",
            is_staff=True,
            is_superuser=True,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=dual,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        response = self.client.post(
            reverse("api-login"),
            {"username": dual.username, "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIs(response.data["user"]["is_superuser"], True)
        self.assertNotIn("is_staff", response.data["user"])

    def test_login_sets_access_token_cookie(self):
        """Verify that login response sets HttpOnly access_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)
        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_login_sets_refresh_token_cookie(self):
        """Verify that login response sets HttpOnly refresh_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_login_keeps_tokens_in_response_body(self):
        """Verify backward compatibility: tokens still in JSON response."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Tokens must still be in response body for mobile/API clients
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class AuthRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Refresh Org", slug="refresh-org")
        self.membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
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

    def test_refresh_rejects_when_last_membership_removed(self):
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data["refresh"]

        self.membership.delete()

        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "no_tenant_membership")

    def test_refresh_accepts_refresh_token_from_cookie(self):
        """Verify that refresh endpoint accepts refresh token from cookie."""
        # Login to get both tokens
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Extract token from cookie instead of body
        self.assertIn("refresh_token", login_response.cookies)
        
        # Create a new client and set the cookie
        new_client = APIClient()
        new_client.cookies["refresh_token"] = login_response.cookies["refresh_token"].value
        
        # Call refresh without providing refresh token in body
        response = new_client.post(
            reverse("api-token-refresh"),
            {},  # Empty body
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_refresh_sets_access_token_cookie(self):
        """Verify that refresh endpoint returns new access token in cookie."""
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
        # Verify new access token is in cookie
        self.assertIn("access_token", response.cookies)
        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_refresh_keeps_token_in_response_body(self):
        """Verify backward compatibility: access token still in JSON response."""
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
        # Token must still be in response body for mobile/API clients
        self.assertIn("access", response.data)


class LogoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Logout Org", slug="logout-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def test_logout_clears_access_token_cookie(self):
        """Verify that logout clears the access_token cookie."""
        # Login first
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", login_response.cookies)
        
        # Call logout
        response = self.client.post(reverse("api-logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cookie is cleared (max_age or expires should be set to immediate deletion)
        self.assertIn("access_token", response.cookies)
        self.assertEqual(response.cookies["access_token"].value, "")

    def test_logout_clears_refresh_token_cookie(self):
        """Verify that logout clears the refresh_token cookie."""
        # Login first
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("refresh_token", login_response.cookies)
        
        # Call logout
        response = self.client.post(reverse("api-logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cookie is cleared
        self.assertIn("refresh_token", response.cookies)
        self.assertEqual(response.cookies["refresh_token"].value, "")

    def test_logout_returns_success_message(self):
        """Verify that logout returns a success response."""
        response = self.client.post(reverse("api-logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("detail", response.data)
        self.assertEqual(response.data["detail"], "Successfully logged out.")


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
        self.tenant = create_tenant(name="Me Org", slug="me-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
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
        self.assertNotIn("is_staff", user_data)
        self.assertIn("is_superuser", user_data)
        self.assertIs(user_data["is_superuser"], False)

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
            role=TenantRole.COORDINATOR,
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
        self.assertEqual(len(response.data["memberships"]), 3)


class ChangePasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Pwd Org", slug="pwd-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
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


class ApiImpersonationTests(TestCase):
    """API JWT impersonation: platform superuser only, audited (WS07)."""

    def setUp(self):
        self.client = APIClient()
        self.tenant = create_tenant(name="Imp Org", slug="imp-org")
        self.member = User.objects.create_user(
            username="imp_member",
            password="pass12345678",
            email="member@imp.test",
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.member,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        self.superuser = User.objects.create_user(
            username="imp_platform_su",
            password="pass12345678",
            email="su@imp.test",
            is_superuser=True,
            is_staff=True,
        )

    def test_staff_without_superuser_cannot_start(self):
        staff_only = User.objects.create_user(
            username="imp_staff_only",
            password="pass12345678",
            email="staff@imp.test",
            is_staff=True,
            is_superuser=False,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=staff_only,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        self.client.force_authenticate(user=staff_only)
        response = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": self.member.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(
            ComplianceAuditLog.objects.filter(
                action=AuditAction.IMPERSONATION_STARTED,
            ).count(),
            0,
        )

    def test_superuser_start_end_writes_audit_log(self):
        started = ComplianceAuditLog.objects.filter(
            action=AuditAction.IMPERSONATION_STARTED,
        ).count()
        ended = ComplianceAuditLog.objects.filter(
            action=AuditAction.IMPERSONATION_ENDED,
        ).count()

        self.client.force_authenticate(user=self.superuser)
        start = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": self.member.pk},
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        self.assertIn("access", start.data)
        imp_access = start.data["access"]
        self.assertEqual(
            ComplianceAuditLog.objects.filter(
                action=AuditAction.IMPERSONATION_STARTED,
            ).count(),
            started + 1,
        )

        # Use cookie for impersonation token (cookie-only auth)
        self.client.force_authenticate(user=None)
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"access_token": imp_access})
        end = cookie_client.post(
            reverse("api-impersonate-end"),
            {},
            format="json",
        )
        self.assertEqual(end.status_code, status.HTTP_200_OK)
        self.assertEqual(
            ComplianceAuditLog.objects.filter(
                action=AuditAction.IMPERSONATION_ENDED,
            ).count(),
            ended + 1,
        )

    def test_cannot_impersonate_superuser_target(self):
        target_su = User.objects.create_user(
            username="imp_target_su",
            password="pass12345678",
            email="targets@imp.test",
            is_superuser=True,
            is_staff=True,
        )
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": target_su.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_impersonate_user_without_membership(self):
        orphan = User.objects.create_user(
            username="imp_no_org",
            password="pass12345678",
            email="orphan@imp.test",
        )
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": orphan.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("membership", response.data["detail"].lower())

    def test_impersonation_me_uses_target_identity(self):
        self.client.force_authenticate(user=self.superuser)
        start = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": self.member.pk},
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        imp_access = start.data["access"]

        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {imp_access}")
        me = self.client.get(reverse("api-me"))
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data["user"]["username"], self.member.username)
        self.assertEqual(len(me.data["memberships"]), 1)
        self.assertEqual(me.data["memberships"][0]["role"], TenantRole.COORDINATOR)

    @override_settings(ENABLE_API_IMPERSONATION=False)
    def test_when_api_impersonation_disabled_start_returns_403(self):
        self.client.force_authenticate(user=self.superuser)
        response = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": self.member.pk},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_end_without_impersonation_claim_returns_400(self):
        ended_before = ComplianceAuditLog.objects.filter(
            action=AuditAction.IMPERSONATION_ENDED,
        ).count()
        login = self.client.post(
            reverse("api-login"),
            {"username": self.member.username, "password": "pass12345678"},
            format="json",
        )
        self.assertEqual(login.status_code, status.HTTP_200_OK)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.data['access']}",
        )
        end = self.client.post(
            reverse("api-impersonate-end"),
            {},
            format="json",
        )
        self.assertEqual(end.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            ComplianceAuditLog.objects.filter(
                action=AuditAction.IMPERSONATION_ENDED,
            ).count(),
            ended_before,
        )

    def test_end_when_operator_demoted_returns_403(self):
        self.client.force_authenticate(user=self.superuser)
        start = self.client.post(
            reverse("api-impersonate-start"),
            {"user_id": self.member.pk},
            format="json",
        )
        self.assertEqual(start.status_code, status.HTTP_200_OK)
        imp_access = start.data["access"]

        self.superuser.is_superuser = False
        self.superuser.save(update_fields=["is_superuser"])

        self.client.force_authenticate(user=None)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {imp_access}")
        end = self.client.post(
            reverse("api-impersonate-end"),
            {},
            format="json",
        )
        self.assertEqual(end.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(end.data.get("code"), "impersonation_invalid_operator")

class CookieAuthenticationMiddlewareTests(TestCase):
    """Test that middleware correctly authenticates requests with cookies (COOKIE-02)."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="middlewareuser",
            password="testpass123",
            email="middleware@test.com",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Middleware Org", slug="middleware-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def _get_tokens(self):
        """Helper to get access and refresh tokens from login."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "middlewareuser", "password": "testpass123"},
            format="json",
        )
        return response.data["access"], response.data["refresh"]

    def test_middleware_authenticates_request_with_cookie(self):
        """Verify middleware correctly sets request.user from access_token cookie."""
        access_token, _ = self._get_tokens()
        
        # Create new client with cookie set
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"access_token": access_token})
        
        # Make request to protected endpoint  
        response = cookie_client.get(reverse("api-me"))
        
        # Should be authenticated via middleware cookie handling
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "middlewareuser")

    def test_middleware_authenticates_with_cookie_only(self):
        """Verify middleware authenticates using cookie (no header support)."""
        access_token, _ = self._get_tokens()
        
        # Create new client with cookie set
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"access_token": access_token})
        
        # Should authenticate via cookie
        response = cookie_client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "middlewareuser")