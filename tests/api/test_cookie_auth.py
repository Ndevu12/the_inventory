"""Tests for cookie-based JWT authentication (COOKIE-02)."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import TenantMembership, TenantRole
from tests.fixtures.factories import create_tenant

User = get_user_model()


class CookieAuthenticationTests(TestCase):
    """Test JWT authentication using HttpOnly cookies."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="cookieuser",
            password="testpass123",
            email="cookie@test.com",
            first_name="Cookie",
            last_name="Tester",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Cookie Org", slug="cookie-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def test_login_sets_access_token_cookie(self):
        """Verify login endpoint sets access_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cookie is set
        self.assertIn("access_token", response.cookies)
        access_token_cookie = response.cookies.get("access_token")
        self.assertIsNotNone(access_token_cookie.value)
        
        # Verify cookie attributes (HttpOnly, Secure, SameSite)
        self.assertTrue(access_token_cookie["httponly"])
        self.assertEqual(access_token_cookie["samesite"], "Lax")
        
        # Verify token is also in response body (backward compatibility)
        self.assertIn("access", response.data)

    def test_login_sets_refresh_token_cookie(self):
        """Verify login endpoint sets refresh_token cookie."""
        response = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify cookie is set
        self.assertIn("refresh_token", response.cookies)
        refresh_token_cookie = response.cookies.get("refresh_token")
        self.assertIsNotNone(refresh_token_cookie.value)
        
        # Verify cookie attributes
        self.assertTrue(refresh_token_cookie["httponly"])
        self.assertEqual(refresh_token_cookie["samesite"], "Lax")
        
        # Verify token is also in response body (backward compatibility)
        self.assertIn("refresh", response.data)

    def test_authenticated_request_with_cookie(self):
        """Verify request with access_token cookie is authenticated."""
        # Login and get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Create a new client and manually set cookies (simulating browser behavior)
        # The APIClient handles cookies automatically in subsequent requests
        cookie_client = APIClient(enforce_csrf_checks=False)
        
        # Make request to /me/ without explicit Authorization header, but with cookies
        response = cookie_client.get(reverse("api-me"))
        
        # Without authentication, should get 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Now set cookie and try again
        access_token = login_response.data["access"]
        cookie_client.cookies.load({"access_token": access_token})
        
        response = cookie_client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "cookieuser")

    def test_header_auth_takes_precedence_over_cookie(self):
        """Verify Authorization header takes precedence over cookie."""
        # Create two users
        user2 = User.objects.create_user(
            username="headeruser",
            password="testpass123",
            email="header@test.com",
            is_staff=True,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=user2,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        
        # Get tokens for both users
        response1 = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        token1 = response1.data["access"]
        
        response2 = self.client.post(
            reverse("api-login"),
            {"username": "headeruser", "password": "testpass123"},
            format="json",
        )
        token2 = response2.data["access"]
        
        # Set cookie to token1 and header to token2
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"access_token": token1})
        cookie_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token2}")
        
        # Should use header token (token2 = headeruser)
        response = cookie_client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "headeruser")

    def test_refresh_with_cookie(self):
        """Verify refresh token from cookie works."""
        # Login
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data["refresh"]
        
        # Create new client and set cookies
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"refresh_token": refresh_token})
        
        # Refresh without sending refresh token in body (relies on cookie)
        response = cookie_client.post(
            reverse("api-token-refresh"),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        
        # New access token should be in cookie
        self.assertIn("access_token", response.cookies)

    def test_invalid_cookie_token_ignored_gracefully(self):
        """Verify invalid cookie tokens don't cause errors."""
        cookie_client = APIClient(enforce_csrf_checks=False)
        cookie_client.cookies.load({"access_token": "invalid.token.here"})
        
        # Should return 401, not 500
        response = cookie_client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_header_still_works_with_new_authenticator(self):
        """Verify header-based JWT still works (backward compatibility)."""
        # Login to get token
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "cookieuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data["access"]
        
        # Use header authentication (traditional method)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get(reverse("api-me"))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "cookieuser")

    def test_no_auth_returns_401(self):
        """Verify protected endpoints require authentication."""
        # Fresh client with no auth
        client = APIClient()
        response = client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
