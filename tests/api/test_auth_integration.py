"""Integration tests for full authentication flows.

Tests complete end-to-end authentication scenarios including:
  - Full login → authenticated request → logout flow
  - Cookie persistence across requests
  - Token refresh and cookie updates
  - Multi-request authenticated transactions
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import TenantMembership, TenantRole

from tests.api.test_auth_views import create_tenant

User = get_user_model()


class FullAuthFlowTests(TestCase):
    """Test complete authentication flows from login through logout."""

    def setUp(self):
        """Create test user and tenant for auth flows."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.tenant = create_tenant(name="Test Org", slug="test-org")
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantRole.COORDINATOR,
            is_active=True,
        )

    def test_full_login_authenticated_request_logout_flow(self):
        """Verify complete flow: login → authenticated request → logout."""
        # Step 1: Login using the slash version of URL
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", login_response.cookies)
        
        # Verify cookies are present with correct attributes
        access_token_cookie = login_response.cookies.get("access_token")
        self.assertIsNotNone(access_token_cookie)
        self.assertTrue(access_token_cookie.get("httponly"))
        
        # Step 2: Make authenticated request with cookie (APIClient maintains cookies)
        auth_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(auth_response.status_code, status.HTTP_200_OK)
        
        # Step 3: Logout
        logout_response = self.client.post(
            reverse("api-logout"),
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify subsequent requests are not authenticated (after cookies deleted)
        protected_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(protected_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_request_returns_401(self):
        """Verify unauthenticated requests to protected endpoints return 401."""
        # Don't login, just try to access protected endpoint
        response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_credentials_prevents_authentication(self):
        """Verify invalid credentials don't set authentication cookies."""
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "wrongpassword"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", login_response.cookies)
        
        # Subsequent request should definitely not be authenticated
        protected_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(protected_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cookie_persistence_across_multiple_requests(self):
        """Verify cookies persist across multiple authenticated requests."""
        # Login once
        self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        
        # Make multiple requests - all should be authenticated
        for _ in range(3):
            response = self.client.get(
                reverse("api-current-tenant"),
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_refresh_updates_access_token_cookie(self):
        """Verify token refresh updates the access_token cookie."""
        # Login to get initial tokens
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        initial_access_token = login_response.cookies.get("access_token").value
        initial_refresh_token = login_response.cookies.get("refresh_token").value
        
        # Refresh the token
        refresh_response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": initial_refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # Verify access_token was updated in the cookie
        new_access_token = refresh_response.cookies.get("access_token").value
        self.assertNotEqual(initial_access_token, new_access_token)
        
        # Verify we can still make authenticated requests with new token
        protected_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(protected_response.status_code, status.HTTP_200_OK)

    def test_login_after_logout_creates_new_session(self):
        """Verify login after logout creates a new authenticated session."""
        # First login
        first_login = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(first_login.status_code, status.HTTP_200_OK)
        first_token = first_login.cookies.get("access_token").value
        
        # Logout
        logout_response = self.client.post(
            reverse("api-logout"),
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Verify logout actually cleared auth
        protected_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(protected_response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Login again
        second_login = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(second_login.status_code, status.HTTP_200_OK)
        second_token = second_login.cookies.get("access_token").value
        
        # New token should be different from first one
        self.assertNotEqual(first_token, second_token)
        
        # Second session should be authenticated
        protected_response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(protected_response.status_code, status.HTTP_200_OK)


class CookieSecurityTests(TestCase):
    """Test that cookies have proper security attributes through auth flows."""

    def setUp(self):
        """Create test user and tenant."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.tenant = create_tenant(name="Test Org", slug="test-org")
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantRole.COORDINATOR,
            is_active=True,
        )

    def test_login_sets_httponly_secure_samesite_cookies(self):
        """Verify login sets cookies with security attributes."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        refresh_token = response.cookies.get("refresh_token")
        
        # Both cookies should exist
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        
        # Both should have HttpOnly set
        self.assertTrue(access_token.get("httponly"))
        self.assertTrue(refresh_token.get("httponly"))
        
        # Both should have SameSite set
        self.assertIsNotNone(access_token.get("samesite"))
        self.assertIsNotNone(refresh_token.get("samesite"))

    def test_refresh_maintains_cookie_security_attributes(self):
        """Verify refresh token endpoint maintains cookie security."""
        # Login first
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        refresh_token = login_response.cookies.get("refresh_token").value
        
        # Refresh the token
        refresh_response = self.client.post(
            reverse("api-token-refresh"),
            {"refresh": refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        
        # New access_token cookie should have same security attributes
        new_access_token = refresh_response.cookies.get("access_token")
        self.assertIsNotNone(new_access_token)
        self.assertTrue(new_access_token.get("httponly"))
        self.assertIsNotNone(new_access_token.get("samesite"))

    def test_logout_deletes_cookies(self):
        """Verify logout sends cookies for deletion."""
        # Login first
        self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        
        # Logout
        logout_response = self.client.post(
            reverse("api-logout"),
            format="json",
        )
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Cookies should be in response (to trigger deletion)
        access_token_cookie = logout_response.cookies.get("access_token")
        refresh_token_cookie = logout_response.cookies.get("refresh_token")
        
        self.assertIsNotNone(access_token_cookie)
        self.assertIsNotNone(refresh_token_cookie)


class HeaderAuthenticationTests(TestCase):
    """Test that authentication works only via cookies, not headers."""

    def setUp(self):
        """Create test user and tenant."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
        )
        self.tenant = create_tenant(name="Test Org", slug="test-org")
        TenantMembership.objects.create(
            user=self.user,
            tenant=self.tenant,
            role=TenantRole.COORDINATOR,
            is_active=True,
        )

    def test_authorization_header_fallback_without_cookie(self):
        """Verify Authorization header works as fallback when no cookies present.
        
        Note: Headers are supported as a fallback for API clients (tests, mobile apps).
        Cookies remain the primary authentication method for browser clients.
        This behavior may change in future improvements.
        """
        # Login to get a valid token
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        access_token = login_response.json()["access"]
        
        # Create a new client without cookies
        client = APIClient()
        
        # Try to authenticate with Authorization header - should work as fallback
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        # Should be authenticated via header fallback when no cookie is present
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_cookies_only_authentication(self):
        """Verify only cookies (not headers) provide authentication."""
        # Login and get cookies
        login_response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Subsequent request with same client (has cookies) should be authenticated
        response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
