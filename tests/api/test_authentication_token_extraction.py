"""Tests for centralized token extraction methods in CookieJWTAuthentication.

These tests verify that the authentication backend provides reusable token
extraction and validation logic that other features can call without
duplicating the extraction logic themselves.
"""

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from rest_framework_simplejwt.tokens import RefreshToken

from api.authentication import CookieJWTAuthentication

User = get_user_model()


class CookieJWTAuthenticationTokenExtractionTests(TestCase):
    """Test centralized token extraction methods for reuse by other features.
    
    These methods provide reusable token extraction logic that other features
    can call without duplicating the extraction logic themselves.
    """

    def setUp(self):
        """Set up test user and authentication instance."""
        self.factory = RequestFactory()
        self.auth = CookieJWTAuthentication()
        
        self.user = User.objects.create_user(
            username="tokenextractiontest",
            email="tokenextractiontest@test.com",
            password="testpass123",
        )
        
        refresh = RefreshToken.for_user(self.user)
        self.valid_token = str(refresh.access_token)

    def test_extract_token_from_cookie_returns_token(self):
        """Verify extract_token_from_cookie retrieves token from cookies."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": self.valid_token}
        
        token = self.auth.extract_token_from_cookie(request)
        
        self.assertEqual(token, self.valid_token)

    def test_extract_token_from_cookie_returns_none_when_missing(self):
        """Verify extract_token_from_cookie returns None when cookie missing."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {}
        
        token = self.auth.extract_token_from_cookie(request)
        
        self.assertIsNone(token)

    def test_extract_token_from_header_returns_token(self):
        """Verify extract_token_from_header retrieves Bearer token from header."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        token = self.auth.extract_token_from_header(request)
        
        self.assertEqual(token, self.valid_token)

    def test_extract_token_from_header_returns_none_when_missing(self):
        """Verify extract_token_from_header returns None when header missing."""
        request = self.factory.get('/api/test/')
        
        token = self.auth.extract_token_from_header(request)
        
        self.assertIsNone(token)

    def test_extract_token_from_header_returns_none_for_different_scheme(self):
        """Verify extract_token_from_header ignores non-Bearer schemes."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Token {self.valid_token}'
        )
        
        token = self.auth.extract_token_from_header(request)
        
        # Should not extract Token scheme, only Bearer
        self.assertIsNone(token)

    def test_extract_token_from_header_returns_none_for_empty_bearer(self):
        """Verify extract_token_from_header handles empty Bearer scheme."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION='Bearer '
        )
        
        token = self.auth.extract_token_from_header(request)
        
        # Should return None for empty token
        self.assertIsNone(token)

    def test_extract_token_prioritizes_cookie(self):
        """Verify extract_token prioritizes cookies when both are present."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION='Bearer different-token'
        )
        request.COOKIES = {"access_token": self.valid_token}
        
        token = self.auth.extract_token(request)
        
        # Should return cookie token, not header token
        self.assertEqual(token, self.valid_token)

    def test_extract_token_falls_back_to_header(self):
        """Verify extract_token falls back to header when no cookie."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        token = self.auth.extract_token(request)
        
        self.assertEqual(token, self.valid_token)

    def test_extract_token_respects_from_cookie_flag(self):
        """Verify extract_token respects from_cookie flag."""
        request = self.factory.get('/api/test/')
        request.COOKIES = {"access_token": self.valid_token}
        
        # With from_cookie=False, should not extract from cookie
        token = self.auth.extract_token(request, from_cookie=False, from_header=False)
        
        self.assertIsNone(token)

    def test_extract_token_respects_from_header_flag(self):
        """Verify extract_token respects from_header flag."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        # With from_header=False, should not extract from header
        token = self.auth.extract_token(request, from_cookie=False, from_header=False)
        
        self.assertIsNone(token)

    def test_validate_and_authenticate_token_returns_user_and_token(self):
        """Verify validate_and_authenticate_token returns user and token."""
        result = self.auth.validate_and_authenticate_token(self.valid_token)
        
        self.assertIsNotNone(result)
        user, token = result
        self.assertEqual(user.id, self.user.id)
        self.assertIsNotNone(token)

    def test_validate_and_authenticate_token_returns_none_for_invalid(self):
        """Verify validate_and_authenticate_token returns None for invalid token."""
        invalid_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.invalid.token"
        
        result = self.auth.validate_and_authenticate_token(invalid_token)
        
        self.assertIsNone(result)

    def test_extract_and_validate_workflow(self):
        """Test complete extraction and validation workflow for feature reuse.
        
        This demonstrates how other features can use the centralized extraction
        and validation methods without duplicating the logic.
        """
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION=f'Bearer {self.valid_token}'
        )
        
        # Step 1: Extract token using centralized method
        token = self.auth.extract_token(request)
        self.assertIsNotNone(token)
        
        # Step 2: Validate and authenticate using centralized method
        result = self.auth.validate_and_authenticate_token(token)
        self.assertIsNotNone(result)
        
        user, validated_token = result
        self.assertEqual(user.id, self.user.id)

    def test_header_fallback_with_invalid_token(self):
        """Verify header fallback handles invalid tokens gracefully."""
        request = self.factory.get(
            '/api/test/',
            HTTP_AUTHORIZATION='Bearer invalid-token-value'
        )
        
        # Extract token
        token = self.auth.extract_token(request)
        self.assertIsNotNone(token)  # Token extracted successfully
        
        # But validation should fail
        result = self.auth.validate_and_authenticate_token(token)
        self.assertIsNone(result)  # Invalid token returns None
