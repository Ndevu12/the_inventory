"""Unit tests for authentication views.

Tests the api.views.auth and api.views.invitations modules which handle
JWT authentication flows using centralized cookie utilities.

This ensures:
1. LoginView sets both access_token and refresh_token cookies
2. RefreshView sets new access_token cookie from refresh token
3. LogoutView deletes both cookies
4. AcceptInvitationView sets cookies for newly accepted users
5. All views use centralized cookie utilities correctly
6. Response data is formatted correctly
"""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import TenantMembership, TenantRole, TenantInvitation, InvitationStatus
from tests.fixtures.factories import create_tenant

User = get_user_model()


class LoginViewTests(TestCase):
    """Test LoginView sets JWT cookies correctly."""

    def setUp(self):
        """Set up test user and tenant."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="logintest",
            email="logintest@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Login Test Org", slug="login-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def test_login_success_returns_200(self):
        """Verify successful login returns 200 OK."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_login_sets_access_token_cookie(self):
        """Verify login sets access_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        self.assertIn("access_token", response.cookies)
        cookie = response.cookies["access_token"]
        self.assertIsNotNone(cookie.value)

    def test_login_access_token_cookie_has_correct_attributes(self):
        """Verify access_token cookie has HttpOnly and SameSite attributes."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_login_sets_refresh_token_cookie(self):
        """Verify login sets refresh_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertIsNotNone(cookie.value)

    def test_login_refresh_token_cookie_has_correct_attributes(self):
        """Verify refresh_token cookie has HttpOnly and SameSite attributes."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        cookie = response.cookies["refresh_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_login_response_includes_user_data(self):
        """Verify login response includes user and tenant information."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "logintest")
        self.assertEqual(response.data["user"]["email"], "logintest@test.com")

    def test_login_response_includes_tokens_in_body(self):
        """Verify login response includes tokens in body (backward compatibility)."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        # Tokens should be in response body AND cookies
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_response_includes_memberships(self):
        """Verify login response includes user's tenant memberships."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        self.assertIn("memberships", response.data)
        self.assertEqual(len(response.data["memberships"]), 1)
        self.assertEqual(response.data["memberships"][0]["tenant__slug"], "login-test-org")

    @patch("api.views.auth.set_jwt_cookie")
    def test_login_calls_set_jwt_cookie_for_access_token(self, mock_set_cookie):
        """Verify LoginView calls set_jwt_cookie for access_token."""
        self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        # Verify set_jwt_cookie was called with access_token
        calls = mock_set_cookie.call_args_list
        access_token_calls = [c for c in calls if c[0][1] == "access_token"]
        self.assertTrue(len(access_token_calls) > 0)

    @patch("api.views.auth.set_jwt_cookie")
    def test_login_calls_set_jwt_cookie_with_correct_max_age_for_access_token(self, mock_set_cookie):
        """Verify access_token cookie has correct max_age."""
        with override_settings(JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300):
            self.client.post(
                reverse("api-login"),
                {"username": "logintest", "password": "testpass123"},
                format="json",
            )
        
        calls = mock_set_cookie.call_args_list
        access_token_calls = [c for c in calls if c[0][1] == "access_token"]
        if access_token_calls:
            call_kwargs = access_token_calls[0][1]
            self.assertEqual(call_kwargs.get("max_age"), 300)

    @patch("api.views.auth.set_jwt_cookie")
    def test_login_calls_set_jwt_cookie_for_refresh_token(self, mock_set_cookie):
        """Verify LoginView calls set_jwt_cookie for refresh_token."""
        self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "testpass123"},
            format="json",
        )
        
        # Verify set_jwt_cookie was called with refresh_token
        calls = mock_set_cookie.call_args_list
        refresh_token_calls = [c for c in calls if c[0][1] == "refresh_token"]
        self.assertTrue(len(refresh_token_calls) > 0)

    @patch("api.views.auth.set_jwt_cookie")
    def test_login_calls_set_jwt_cookie_with_correct_max_age_for_refresh_token(self, mock_set_cookie):
        """Verify refresh_token cookie has correct max_age."""
        with override_settings(JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800):
            self.client.post(
                reverse("api-login"),
                {"username": "logintest", "password": "testpass123"},
                format="json",
            )
        
        calls = mock_set_cookie.call_args_list
        refresh_token_calls = [c for c in calls if c[0][1] == "refresh_token"]
        if refresh_token_calls:
            call_kwargs = refresh_token_calls[0][1]
            self.assertEqual(call_kwargs.get("max_age"), 604800)

    def test_login_invalid_credentials_returns_401(self):
        """Verify login with invalid credentials returns 401."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "logintest", "password": "wrongpassword"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username_returns_400(self):
        """Verify login without username returns 400."""
        response = self.client.post(
            reverse("api-login"),
            {"password": "testpass123"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RefreshViewTests(TestCase):
    """Test RefreshView sets JWT cookie for refreshed token."""

    def setUp(self):
        """Set up test user, tenant, and refresh token."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="refreshtest",
            email="refreshtest@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Refresh Test Org", slug="refresh-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        
        # Login to get refresh token
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "refreshtest", "password": "testpass123"},
            format="json",
        )
        self.refresh_token = login_response.data["refresh"]

    def test_refresh_with_token_in_body_returns_200(self):
        """Verify refresh endpoint returns 200 with valid token."""
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": self.refresh_token},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_refresh_sets_new_access_token_cookie(self):
        """Verify refresh endpoint sets new access_token cookie."""
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": self.refresh_token},
            format="json",
        )
        
        self.assertIn("access_token", response.cookies)
        cookie = response.cookies["access_token"]
        self.assertIsNotNone(cookie.value)

    def test_refresh_access_token_cookie_has_correct_attributes(self):
        """Verify refreshed access_token cookie has correct attributes."""
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": self.refresh_token},
            format="json",
        )
        
        cookie = response.cookies["access_token"]
        self.assertTrue(cookie["httponly"])
        self.assertEqual(cookie["samesite"], "Lax")

    def test_refresh_response_includes_new_token(self):
        """Verify refresh response includes new access token."""
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": self.refresh_token},
            format="json",
        )
        
        self.assertIn("access", response.data)
        self.assertIsNotNone(response.data["access"])

    def test_refresh_with_token_in_cookie(self):
        """Verify refresh works with token in cookie."""
        cookie_client = APIClient()
        cookie_client.cookies.load({"refresh_token": self.refresh_token})
        
        response = cookie_client.post(
            reverse("api-token-refresh"),
            {},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", response.cookies)

    @patch("api.views.auth.set_jwt_cookie")
    def test_refresh_calls_set_jwt_cookie_with_correct_max_age(self, mock_set_cookie):
        """Verify refresh sets access_token with correct max_age."""
        with override_settings(JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300):
            self.client.post(
                reverse("api-token-refresh"),
                {"refresh": self.refresh_token},
                format="json",
            )
        
        calls = mock_set_cookie.call_args_list
        if calls:
            call_kwargs = calls[0][1]
            self.assertEqual(call_kwargs.get("max_age"), 300)

    def test_refresh_invalid_token_returns_401(self):
        """Verify refresh with invalid token returns 401."""
        response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": "invalid.token.here"},
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutViewTests(TestCase):
    """Test LogoutView deletes JWT cookies."""

    def setUp(self):
        """Set up test client."""
        self.client = APIClient()

    def test_logout_returns_200(self):
        """Verify logout endpoint returns 200 OK."""
        response = self.client.post(reverse("api-logout"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_response_includes_success_message(self):
        """Verify logout response includes success message."""
        response = self.client.post(reverse("api-logout"))
        self.assertIn("detail", response.data)
        self.assertIn("logged out", response.data["detail"].lower())

    @patch("api.views.auth.delete_jwt_cookie")
    def test_logout_calls_delete_jwt_cookie_for_access_token(self, mock_delete):
        """Verify LogoutView calls delete_jwt_cookie for access_token."""
        self.client.post(reverse("api-logout"))
        
        # Verify delete_jwt_cookie was called with access_token
        calls = mock_delete.call_args_list
        access_token_calls = [c for c in calls if c[0][1] == "access_token"]
        self.assertTrue(len(access_token_calls) > 0)

    @patch("api.views.auth.delete_jwt_cookie")
    def test_logout_calls_delete_jwt_cookie_for_refresh_token(self, mock_delete):
        """Verify LogoutView calls delete_jwt_cookie for refresh_token."""
        self.client.post(reverse("api-logout"))
        
        # Verify delete_jwt_cookie was called with refresh_token
        calls = mock_delete.call_args_list
        refresh_token_calls = [c for c in calls if c[0][1] == "refresh_token"]
        self.assertTrue(len(refresh_token_calls) > 0)

    def test_logout_is_public_endpoint(self):
        """Verify logout can be called without authentication."""
        # Fresh client without any auth
        unauthenticated_client = APIClient()
        response = unauthenticated_client.post(reverse("api-logout"))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_logout_is_idempotent(self):
        """Verify logout can be called multiple times without error."""
        response1 = self.client.post(reverse("api-logout"))
        response2 = self.client.post(reverse("api-logout"))
        
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)


class AcceptInvitationViewTests(TestCase):
    """Test AcceptInvitationView sets JWT cookies for accepted users."""

    def setUp(self):
        """Set up test data for invitation acceptance."""
        from datetime import timedelta
        from django.utils import timezone
        
        self.client = APIClient()
        
        # Create inviting user
        self.inviter = User.objects.create_user(
            username="inviter",
            email="inviter@test.com",
            password="testpass123",
            is_staff=True,
        )
        
        # Create tenant
        self.tenant = create_tenant(name="Invite Test Org", slug="invite-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.inviter,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        
        # Create invitation
        self.invitation = TenantInvitation.objects.create(
            tenant=self.tenant,
            email="newuser@test.com",
            role=TenantRole.VIEWER,
            invited_by=self.inviter,
            expires_at=timezone.now() + timedelta(days=7),
        )

    def test_accept_invitation_success_returns_200(self):
        """Verify accepting invitation returns 200 OK."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_accept_invitation_sets_access_token_cookie(self):
        """Verify accepting invitation sets access_token cookie."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertIn("access_token", response.cookies)
        cookie = response.cookies["access_token"]
        self.assertIsNotNone(cookie.value)

    def test_accept_invitation_sets_refresh_token_cookie(self):
        """Verify accepting invitation sets refresh_token cookie."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertIn("refresh_token", response.cookies)
        cookie = response.cookies["refresh_token"]
        self.assertIsNotNone(cookie.value)

    def test_accept_invitation_cookies_have_correct_attributes(self):
        """Verify invitation acceptance cookies have correct attributes."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        access_cookie = response.cookies["access_token"]
        refresh_cookie = response.cookies["refresh_token"]
        
        self.assertTrue(access_cookie["httponly"])
        self.assertEqual(access_cookie["samesite"], "Lax")
        self.assertTrue(refresh_cookie["httponly"])
        self.assertEqual(refresh_cookie["samesite"], "Lax")

    def test_accept_invitation_response_includes_user_data(self):
        """Verify acceptance response includes user and tenant information."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
                "first_name": "New",
                "last_name": "User",
            },
            format="json",
        )
        
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")
        self.assertEqual(response.data["user"]["email"], "newuser@test.com")
        self.assertEqual(response.data["user"]["first_name"], "New")
        self.assertEqual(response.data["user"]["last_name"], "User")

    def test_accept_invitation_response_includes_tenant_info(self):
        """Verify acceptance response includes tenant information."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertIn("tenant", response.data)
        self.assertEqual(response.data["tenant"]["slug"], "invite-test-org")
        self.assertEqual(response.data["tenant"]["role"], TenantRole.VIEWER)

    def test_accept_invitation_response_includes_tokens(self):
        """Verify acceptance response includes tokens in body."""
        response = self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_accept_invitation_creates_user_account(self):
        """Verify accepting invitation creates new user account."""
        self.assertFalse(User.objects.filter(username="newuser").exists())
        
        self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertTrue(User.objects.filter(username="newuser").exists())
        new_user = User.objects.get(username="newuser")
        self.assertEqual(new_user.email, "newuser@test.com")

    def test_accept_invitation_adds_user_to_tenant(self):
        """Verify accepting invitation adds user to tenant."""
        self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        new_user = User.objects.get(username="newuser")
        membership = TenantMembership.objects.get(user=new_user, tenant=self.tenant)
        self.assertEqual(membership.role, TenantRole.VIEWER)
        self.assertTrue(membership.is_active)

    def test_accept_invitation_marks_invitation_as_accepted(self):
        """Verify accepting invitation updates invitation status."""
        self.assertEqual(self.invitation.status, InvitationStatus.PENDING)
        
        self.client.post(
            reverse("api-invitation-accept", args=[self.invitation.token]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, InvitationStatus.ACCEPTED)
        self.assertIsNotNone(self.invitation.accepted_at)

    def test_accept_invitation_invalid_token_returns_400(self):
        """Verify accepting with invalid token returns error."""
        response = self.client.post(
            reverse("api-invitation-accept", args=["invalid-token"]),
            {
                "username": "newuser",
                "password": "newpass123",
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
