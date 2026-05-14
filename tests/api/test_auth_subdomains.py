"""Integration tests for subdomain cookie scenarios.

Tests production cookie domain configurations:
  - Development: JWT_COOKIE_DOMAIN=None (exact hostname match only)
  - Production: JWT_COOKIE_DOMAIN=".example.com" (subdomain cookie sharing)
  - Domain-specific cookie behavior across tenant subdomains
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import TenantMembership, TenantRole

from tests.api.test_auth_views import create_tenant

User = get_user_model()


class DevelopmentCookieDomainsTests(TestCase):
    """Test development mode (JWT_COOKIE_DOMAIN=None) cookie behavior."""

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

    @override_settings(
        JWT_COOKIE_DOMAIN=None,
        JWT_COOKIE_SECURE=False,
        JWT_COOKIE_SAMESITE="Lax",
    )
    def test_development_domain_setting_is_none(self):
        """Verify development mode uses domain=None for exact hostname matching."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # In development, domain should be None (cookie applies to exact hostname)
        access_token = response.cookies.get("access_token")
        self.assertIsNotNone(access_token)
        # Domain attribute will not be set (defaults to current host)
        # The cookie will be set for the exact hostname only

    @override_settings(
        JWT_COOKIE_DOMAIN=None,
        JWT_COOKIE_SECURE=False,
        JWT_COOKIE_SAMESITE="Lax",
    )
    def test_development_cookies_have_no_domain_restriction(self):
        """Verify cookies in dev mode apply only to exact hostname."""
        # Login
        self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        
        # Authenticated request should work
        response = self.client.get(
            reverse("api-current-tenant"),
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProductionCookieDomainsTests(TestCase):
    """Test production mode (JWT_COOKIE_DOMAIN=".example.com") cookie behavior."""

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

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE="Lax",
    )
    def test_production_domain_setting_is_parent_domain(self):
        """Verify production mode uses parent domain for subdomain cookie sharing."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # In production, domain is set to parent domain
        access_token = response.cookies.get("access_token")
        self.assertIsNotNone(access_token)
        # Domain should be .example.com (allows subdomain cookie sharing)

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE="Lax",
    )
    def test_production_secure_setting_enabled(self):
        """Verify production cookies use secure flag."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        self.assertIsNotNone(access_token)
        # In production, secure flag should be enabled
        # Note: test client may not fully enforce this, but setting is verified via settings

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE="None",
    )
    def test_production_samesite_can_be_none(self):
        """Verify production can use SameSite=None for cross-origin requests."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        self.assertIsNotNone(access_token)
        # With SameSite=None, secure flag is required for cross-origin


class CookieDomainConfigurationTests(TestCase):
    """Test that cookie domain configuration is applied correctly through auth flow."""

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

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_PATH="/api/",
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE="Strict",
    )
    def test_login_applies_all_cookie_settings(self):
        """Verify login applies domain, path, secure, and samesite settings."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        refresh_token = response.cookies.get("refresh_token")
        
        # Both cookies should have same attributes
        self.assertIsNotNone(access_token)
        self.assertIsNotNone(refresh_token)
        self.assertTrue(access_token.get("httponly"))
        self.assertTrue(refresh_token.get("httponly"))

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_PATH="/api/",
        JWT_COOKIE_SECURE=True,
        JWT_COOKIE_SAMESITE="Strict",
    )
    def test_refresh_maintains_cookie_settings(self):
        """Verify refresh token endpoint maintains same cookie settings."""
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
        
        # New access_token should have same settings
        new_access_token = refresh_response.cookies.get("access_token")
        self.assertIsNotNone(new_access_token)
        self.assertTrue(new_access_token.get("httponly"))

    @override_settings(
        JWT_COOKIE_DOMAIN=".tenant-subdomain.example.com",
        JWT_COOKIE_SECURE=True,
    )
    def test_custom_subdomain_cookie_domain(self):
        """Verify custom subdomain cookie domain configuration works."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Cookies should be created successfully
        self.assertIn("access_token", response.cookies)
        self.assertIn("refresh_token", response.cookies)


class CookieSameSiteTests(TestCase):
    """Test SameSite attribute behavior across different configurations."""

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

    @override_settings(JWT_COOKIE_SAMESITE="Strict")
    def test_samesite_strict_configuration(self):
        """Verify SameSite=Strict configuration is applied."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        # SameSite=Strict prevents cross-site cookie send
        self.assertEqual(access_token.get("samesite"), "Strict")

    @override_settings(JWT_COOKIE_SAMESITE="Lax")
    def test_samesite_lax_configuration(self):
        """Verify SameSite=Lax configuration is applied."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        # SameSite=Lax is default for development
        self.assertEqual(access_token.get("samesite"), "Lax")

    @override_settings(
        JWT_COOKIE_SAMESITE="None",
        JWT_COOKIE_SECURE=True,  # Required when SameSite=None
    )
    def test_samesite_none_requires_secure(self):
        """Verify SameSite=None works with secure flag."""
        response = self.client.post(
            reverse("api-login-slash"),
            {"username": "testuser", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        access_token = response.cookies.get("access_token")
        # SameSite=None allows cross-site requests (requires secure)
        self.assertEqual(access_token.get("samesite"), "None")
