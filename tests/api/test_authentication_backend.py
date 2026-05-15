"""Unit tests for CookieJWTAuthentication backend.

Tests the api.authentication module which provides JWT authentication with:
- Primary method: HttpOnly cookies (preferred for browser-based clients)
- Fallback method: Authorization headers (for API clients, tests, mobile apps)

This ensures:
1. Authentication prioritizes cookies over headers
2. Authorization headers work as a fallback when no cookie is present
3. Invalid tokens are handled gracefully
4. User objects are retrieved correctly from valid tokens
5. Authentication returns None when no token is found
6. Token extraction logic is centralized and reusable
"""



from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import RefreshToken

from api.authentication import CookieJWTAuthentication
from tenants.models import TenantMembership, TenantRole
from tests.fixtures.factories import create_tenant

User = get_user_model()


class CookieJWTAuthenticationTests(TestCase):
    """Test CookieJWTAuthentication backend for cookie-only JWT auth."""

    def setUp(self):
        """Set up test user, tenant, and authentication instance."""
        self.factory = RequestFactory()
        self.auth = CookieJWTAuthentication()
        
        self.user = User.objects.create_user(
            username="authtest",
            email="authtest@test.com",
            password="testpass123",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Auth Test Org", slug="auth-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        
        # Generate valid JWT token for testing
        refresh = RefreshToken.for_user(self.user)
        self.valid_token = str(refresh.access_token)
        self.invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"

    def test_authenticate_returns_none_when_no_token_in_cookie(self):
        """Verify authenticate returns None when access_token cookie missing."""
        request = self.factory.get('/api/test/')
        # No cookies set
        
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_returns_none_when_cookie_dict_empty(self):
        """Verify authenticate returns None when cookies dict is empty."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {}
        
        result = self.auth.authenticate(request)
        self.assertIsNone(result)

    def test_authenticate_returns_user_and_token_with_valid_cookie(self):
        """Verify authenticate returns (user, token) with valid access_token cookie."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": self.valid_token}
        
        result = self.auth.authenticate(request)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        user, token = result
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(user.username, self.user.username)
        self.assertIsNotNone(token)

    def test_authenticate_returns_none_when_invalid_token_in_cookie(self):
        """Verify authenticate returns None when token is invalid (catches InvalidToken)."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": self.invalid_token}
        
        result = self.auth.authenticate(request)
        
        # Should return None, not raise exception (let view handle 401)
        self.assertIsNone(result)


    def test_authenticate_header_fallback_when_no_cookie(self):
        """Verify Authorization header is used as fallback when no cookie present.
        
        Note: This is a fallback feature for API clients, not the primary method.
        Future improvements may adjust or remove this behavior.
        """
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        # No cookies set - should use header as fallback
        
        result = self.auth.authenticate(request)
        
        # Should authenticate via header when no cookie is present
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)

    def test_authenticate_prioritizes_cookie_over_header(self):
        """Verify cookies are prioritized over Authorization headers.
        
        When both cookie and header are present, cookie takes precedence.
        """
        # Create two users with different tokens
        user2 = User.objects.create_user(
            username="headeruser",
            email="headeruser@test.com",
            password="testpass123",
            is_staff=True,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=user2,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )
        
        refresh2 = RefreshToken.for_user(user2)
        token2 = str(refresh2.access_token)
        
        # Set cookie to user1's token and header to user2's token
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {token2}'
        )
        request.COOKIES = {"access_token": self.valid_token}
        
        result = self.auth.authenticate(request)
        
        # Should authenticate as user1 (from cookie), not user2 (from header)
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)

    def test_get_validated_token_validates_successfully(self):
        """Verify get_validated_token validates correct tokens."""
        validated = self.auth.get_validated_token(self.valid_token)
        self.assertIsNotNone(validated)

    def test_get_validated_token_raises_invalid_token_for_bad_token(self):
        """Verify get_validated_token raises InvalidToken for invalid token."""
        with self.assertRaises(InvalidToken):
            self.auth.get_validated_token(self.invalid_token)

    def test_get_validated_token_raises_invalid_token_for_malformed_token(self):
        """Verify get_validated_token raises InvalidToken for malformed token."""
        with self.assertRaises(InvalidToken):
            self.auth.get_validated_token("not.a.token")

    def test_get_validated_token_raises_invalid_token_for_empty_string(self):
        """Verify get_validated_token raises InvalidToken for empty string."""
        with self.assertRaises(InvalidToken):
            self.auth.get_validated_token("")

    def test_get_validated_token_error_message_includes_details(self):
        """Verify InvalidToken exception includes error details."""
        try:
            self.auth.get_validated_token(self.invalid_token)
            self.fail("Expected InvalidToken to be raised")
        except InvalidToken as e:
            # Error message should include "Invalid token:"
            self.assertIn("Invalid token:", str(e))

    def test_authenticate_with_empty_string_token(self):
        """Verify authenticate handles empty string token gracefully."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": ""}
        
        # Empty string is truthy for "get('access_token')" but fails validation
        # The token will be attempted to validate, which will fail gracefully
        result = self.auth.authenticate(request)
        
        # Should return None (invalid token handled gracefully)
        self.assertIsNone(result)

    def test_authenticate_with_none_token_value(self):
        """Verify authenticate handles None cookie value."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": None}
        
        result = self.auth.authenticate(request)
        
        # None value should be handled (None is falsy, so `is not None` check passes)
        # But then it will try to validate None which fails
        self.assertIsNone(result)

    def test_authenticate_returns_correct_user_object(self):
        """Verify authenticate returns the exact user object from token."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": self.valid_token}
        
        result = self.auth.authenticate(request)
        
        self.assertIsNotNone(result)
        user, token = result
        
        # Verify it's the correct user
        self.assertEqual(user.username, "authtest")
        self.assertEqual(user.email, "authtest@test.com")
        self.assertEqual(user.is_staff, True)

    def test_authenticate_with_multiple_users_same_tenant(self):
        """Verify authentication works correctly with multiple users."""
        user2 = User.objects.create_user(
            username="authtest2",
            email="authtest2@test.com",
            password="testpass123",
            is_staff=True,
        )
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=user2,
            role=TenantRole.VIEWER,
            is_active=True,
            is_default=True,
        )
        
        refresh2 = RefreshToken.for_user(user2)
        token2 = str(refresh2.access_token)
        
        # Test authentication for user1
        request1 = self.factory.get('/api/test/')
        request1.COOKIES = {"access_token": self.valid_token}
        
        result1 = self.auth.authenticate(request1)
        self.assertEqual(result1[0].id, self.user.id)
        
        # Test authentication for user2
        request2 = self.factory.get('/api/test/')
        request2.COOKIES = {"access_token": token2}
        
        result2 = self.auth.authenticate(request2)
        self.assertEqual(result2[0].id, user2.id)
        
        # Results should be different
        self.assertNotEqual(result1[0].id, result2[0].id)

    def test_authenticate_does_not_modify_request(self):
        """Verify authenticate does not modify the request object."""
        request = self.factory.get('/api/test/')
        original_cookies = {"access_token": self.valid_token}
        request.COOKIES = original_cookies.copy()
        
        original_method = request.method
        original_path = request.path
        
        self.auth.authenticate(request)
        
        # Verify request is unchanged
        self.assertEqual(request.method, original_method)
        self.assertEqual(request.path, original_path)
        self.assertEqual(request.COOKIES, original_cookies)


class CookieJWTAuthenticationEdgeCasesTests(TestCase):
    """Test edge cases and error handling for CookieJWTAuthentication."""

    def setUp(self):
        """Set up test user and authentication instance."""
        self.factory = RequestFactory()
        self.auth = CookieJWTAuthentication()
        
        self.user = User.objects.create_user(
            username="edgecase",
            email="edgecase@test.com",
            password="testpass123",
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.valid_token = str(refresh.access_token)

    def test_authenticate_with_whitespace_only_token(self):
        """Verify authenticate handles whitespace-only tokens."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": "   "}
        
        result = self.auth.authenticate(request)
        
        # Whitespace token should fail validation gracefully
        self.assertIsNone(result)

    def test_authenticate_with_other_cookies_present(self):
        """Verify authenticate works correctly with other cookies present."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {
            "access_token": self.valid_token,
            "refresh_token": "some_refresh_token",
            "session_id": "some_session",
            "other_cookie": "other_value",
        }
        
        result = self.auth.authenticate(request)
        
        # Should still authenticate successfully
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)

    def test_authenticate_cookie_name_is_case_sensitive(self):
        """Verify cookie name lookup is case-sensitive."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"Access_Token": self.valid_token}  # Wrong case
        
        result = self.auth.authenticate(request)
        
        # Should not authenticate (cookie name must be exactly "access_token")
        self.assertIsNone(result)

    def test_get_validated_token_with_none_input(self):
        """Verify get_validated_token handles None input."""
        # None might be silently passed through or raise an error depending on parent implementation
        # The important thing is authenticate() handles it gracefully
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": None}
        
        result = self.auth.authenticate(request)
        # Should return None for None token
        self.assertIsNone(result)

    def test_authenticate_with_user_deleted_after_token_creation(self):
        """Verify authentication fails when user is deleted."""
        from rest_framework_simplejwt.exceptions import AuthenticationFailed
        
        # Create a token
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        
        # Delete the user
        self.user.delete()
        
        # Try to authenticate with deleted user's token
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": token}
        
        # Should raise AuthenticationFailed because user doesn't exist
        # The parent class get_user raises this, not caught by CookieJWTAuthentication
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)

    def test_authenticate_with_inactive_user(self):
        """Verify authentication fails for inactive users."""
        from rest_framework_simplejwt.exceptions import AuthenticationFailed
        
        self.user.is_active = False
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        token = str(refresh.access_token)
        
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": token}
        
        # Parent class get_user raises AuthenticationFailed for inactive users
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(request)


class CookieJWTAuthenticationIntegrationTests(TestCase):
    """Integration tests for CookieJWTAuthentication with real token lifecycle."""

    def setUp(self):
        """Set up test user and authentication instance."""
        self.factory = RequestFactory()
        self.auth = CookieJWTAuthentication()
        
        self.user = User.objects.create_user(
            username="integration",
            email="integration@test.com",
            password="testpass123",
        )

    def test_full_authentication_flow(self):
        """Test complete authentication flow: generate token -> authenticate -> verify."""
        # Step 1: Generate token (simulating login)
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Step 2: Set token in cookie (simulating browser storing cookie)
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": access_token}
        
        # Step 3: Authenticate request (simulating protected endpoint)
        result = self.auth.authenticate(request)
        
        # Step 4: Verify authentication succeeded
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(user.username, "integration")

    def test_token_validation_preserves_user_data(self):
        """Verify token contains and resolves to correct user data."""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": access_token}
        
        result = self.auth.authenticate(request)
        authenticated_user, _ = result
        
        # Verify all user properties are preserved
        self.assertEqual(authenticated_user.username, self.user.username)
        self.assertEqual(authenticated_user.email, self.user.email)
        self.assertEqual(authenticated_user.is_staff, self.user.is_staff)
        self.assertEqual(authenticated_user.is_active, self.user.is_active)


