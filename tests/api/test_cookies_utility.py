"""Unit tests for centralized JWT cookie utilities.

Tests the api.utils.cookies module which provides centralized management
of JWT cookie operations across the authentication system.

This ensures:
1. Cookie parameters are consistent and read from Django settings
2. All views use the same cookie configuration
3. Cookie domain, path, secure, samesite, and httponly attributes are handled correctly
4. Both setting and deleting cookies use matching parameters
"""

from unittest.mock import patch

from django.test import TestCase, override_settings
from rest_framework.response import Response

from api.utils.cookies import delete_jwt_cookie, get_jwt_cookie_params, set_jwt_cookie


class GetJWTCookieParamsTests(TestCase):
    """Test get_jwt_cookie_params() returns correct configuration from settings."""

    def test_returns_dict_with_all_required_keys(self):
        """Verify function returns dict with all required cookie parameter keys."""
        params = get_jwt_cookie_params()
        
        required_keys = {"domain", "path", "secure", "samesite", "httponly"}
        self.assertEqual(set(params.keys()), required_keys)

    def test_httponly_always_true(self):
        """Verify httponly is always True for security."""
        params = get_jwt_cookie_params()
        self.assertTrue(params["httponly"])

    def test_default_path_is_root(self):
        """Verify default path is '/' when not configured."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["path"], "/")

    def test_default_samesite_is_lax(self):
        """Verify default SameSite is 'Lax' when not configured."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["samesite"], "Lax")

    def test_default_domain_is_none(self):
        """Verify default domain is None (exact hostname match)."""
        params = get_jwt_cookie_params()
        self.assertIsNone(params["domain"])

    @override_settings(DEBUG=True)
    def test_secure_false_in_development(self):
        """Verify secure is False when DEBUG=True."""
        params = get_jwt_cookie_params()
        self.assertFalse(params["secure"])

    @override_settings(DEBUG=False)
    def test_secure_false_when_debug_false(self):
        """Verify secure can be False in production when not configured."""
        # By default, JWT_COOKIE_SECURE defaults to False unless explicitly set
        params = get_jwt_cookie_params()
        self.assertFalse(params["secure"])

    @override_settings(JWT_COOKIE_DOMAIN="localhost")
    def test_reads_custom_domain_from_settings(self):
        """Verify function reads JWT_COOKIE_DOMAIN from Django settings."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["domain"], "localhost")

    @override_settings(JWT_COOKIE_DOMAIN=".example.com")
    def test_reads_subdomain_cookie_domain(self):
        """Verify function reads subdomain cookie domain (.example.com)."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["domain"], ".example.com")

    @override_settings(JWT_COOKIE_PATH="/api/")
    def test_reads_custom_path_from_settings(self):
        """Verify function reads JWT_COOKIE_PATH from Django settings."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["path"], "/api/")

    @override_settings(JWT_COOKIE_SAMESITE="Strict")
    def test_reads_custom_samesite_from_settings(self):
        """Verify function reads JWT_COOKIE_SAMESITE from Django settings."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["samesite"], "Strict")

    @override_settings(JWT_COOKIE_SAMESITE="None")
    def test_reads_samesite_none_for_cross_origin(self):
        """Verify function reads JWT_COOKIE_SAMESITE='None' for cross-origin."""
        params = get_jwt_cookie_params()
        self.assertEqual(params["samesite"], "None")

    @override_settings(JWT_COOKIE_SECURE=True)
    def test_reads_secure_true_from_settings(self):
        """Verify function reads JWT_COOKIE_SECURE=True from Django settings."""
        params = get_jwt_cookie_params()
        self.assertTrue(params["secure"])

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_PATH="/api/v1/",
        JWT_COOKIE_SAMESITE="Strict",
        JWT_COOKIE_SECURE=True,
    )
    def test_reads_all_custom_settings(self):
        """Verify function reads all custom settings correctly."""
        params = get_jwt_cookie_params()
        
        self.assertEqual(params["domain"], ".example.com")
        self.assertEqual(params["path"], "/api/v1/")
        self.assertEqual(params["samesite"], "Strict")
        self.assertTrue(params["secure"])
        self.assertTrue(params["httponly"])


class SetJWTCookieTests(TestCase):
    """Test set_jwt_cookie() sets cookies with correct parameters."""

    def setUp(self):
        """Set up test response object."""
        self.response = Response({"status": "ok"})

    def test_calls_response_set_cookie(self):
        """Verify set_jwt_cookie calls response.set_cookie()."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            mock_set.assert_called_once()

    def test_passes_correct_key_and_value(self):
        """Verify set_jwt_cookie passes correct key and value."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_args = mock_set.call_args
            self.assertEqual(call_args[0][0], "access_token")
            self.assertEqual(call_args[0][1], "token123")

    def test_passes_max_age_parameter(self):
        """Verify set_jwt_cookie passes max_age parameter."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertEqual(call_kwargs["max_age"], 300)

    def test_passes_httponly_true(self):
        """Verify set_jwt_cookie sets httponly=True."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertTrue(call_kwargs["httponly"])

    def test_passes_all_cookie_parameters(self):
        """Verify set_jwt_cookie passes all required parameters."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            required_keys = {"domain", "path", "secure", "samesite", "httponly", "max_age"}
            self.assertEqual(set(call_kwargs.keys()), required_keys)

    @override_settings(JWT_COOKIE_DOMAIN="localhost")
    def test_sets_cookie_with_custom_domain(self):
        """Verify set_jwt_cookie uses custom domain from settings."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertEqual(call_kwargs["domain"], "localhost")

    @override_settings(JWT_COOKIE_PATH="/api/")
    def test_sets_cookie_with_custom_path(self):
        """Verify set_jwt_cookie uses custom path from settings."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertEqual(call_kwargs["path"], "/api/")

    @override_settings(JWT_COOKIE_SAMESITE="Strict")
    def test_sets_cookie_with_custom_samesite(self):
        """Verify set_jwt_cookie uses custom SameSite from settings."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertEqual(call_kwargs["samesite"], "Strict")

    @override_settings(JWT_COOKIE_SECURE=True)
    def test_sets_cookie_with_secure_true(self):
        """Verify set_jwt_cookie uses secure=True from settings."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            
            call_kwargs = mock_set.call_args[1]
            self.assertTrue(call_kwargs["secure"])

    def test_different_max_ages_for_access_and_refresh(self):
        """Verify set_jwt_cookie works with different max_age values."""
        with patch.object(self.response, "set_cookie") as mock_set:
            # Access token: 5 minutes
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            self.assertEqual(mock_set.call_args_list[0][1]["max_age"], 300)
            
            # Refresh token: 7 days
            set_jwt_cookie(self.response, "refresh_token", "token456", max_age=604800)
            self.assertEqual(mock_set.call_args_list[1][1]["max_age"], 604800)

    def test_sets_multiple_cookies_on_same_response(self):
        """Verify set_jwt_cookie can be called multiple times on same response."""
        with patch.object(self.response, "set_cookie") as mock_set:
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            set_jwt_cookie(self.response, "refresh_token", "token456", max_age=604800)
            
            self.assertEqual(mock_set.call_count, 2)
            first_call = mock_set.call_args_list[0]
            second_call = mock_set.call_args_list[1]
            
            self.assertEqual(first_call[0][0], "access_token")
            self.assertEqual(second_call[0][0], "refresh_token")


class DeleteJWTCookieTests(TestCase):
    """Test delete_jwt_cookie() deletes cookies with matching parameters."""

    def setUp(self):
        """Set up test response object."""
        self.response = Response({"status": "ok"})

    def test_calls_response_delete_cookie(self):
        """Verify delete_jwt_cookie calls response.delete_cookie()."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            mock_delete.assert_called_once()

    def test_passes_correct_key(self):
        """Verify delete_jwt_cookie passes correct cookie key."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_args = mock_delete.call_args
            self.assertEqual(call_args[0][0], "access_token")

    def test_passes_all_matching_parameters(self):
        """Verify delete_jwt_cookie passes domain, path, samesite parameters."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_kwargs = mock_delete.call_args[1]
            # delete_cookie should have domain, path, samesite (not secure, httponly, max_age)
            required_keys = {"domain", "path", "samesite"}
            self.assertEqual(set(call_kwargs.keys()), required_keys)

    @override_settings(JWT_COOKIE_DOMAIN="localhost")
    def test_deletes_cookie_with_matching_domain(self):
        """Verify delete_jwt_cookie uses same domain as set_jwt_cookie."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_kwargs = mock_delete.call_args[1]
            self.assertEqual(call_kwargs["domain"], "localhost")

    @override_settings(JWT_COOKIE_PATH="/api/")
    def test_deletes_cookie_with_matching_path(self):
        """Verify delete_jwt_cookie uses same path as set_jwt_cookie."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_kwargs = mock_delete.call_args[1]
            self.assertEqual(call_kwargs["path"], "/api/")

    @override_settings(JWT_COOKIE_SAMESITE="Strict")
    def test_deletes_cookie_with_matching_samesite(self):
        """Verify delete_jwt_cookie uses same SameSite as set_jwt_cookie."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_kwargs = mock_delete.call_args[1]
            self.assertEqual(call_kwargs["samesite"], "Strict")

    def test_parameter_consistency_between_set_and_delete(self):
        """Verify set and delete use same domain, path, samesite parameters."""
        with patch.object(self.response, "set_cookie") as mock_set, \
             patch.object(self.response, "delete_cookie") as mock_delete:
            
            set_jwt_cookie(self.response, "access_token", "token123", max_age=300)
            delete_jwt_cookie(self.response, "access_token")
            
            set_kwargs = mock_set.call_args[1]
            delete_kwargs = mock_delete.call_args[1]
            
            # These must match for browsers to delete the cookie
            self.assertEqual(set_kwargs["domain"], delete_kwargs["domain"])
            self.assertEqual(set_kwargs["path"], delete_kwargs["path"])
            self.assertEqual(set_kwargs["samesite"], delete_kwargs["samesite"])

    def test_delete_multiple_cookies_on_same_response(self):
        """Verify delete_jwt_cookie can be called multiple times."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            delete_jwt_cookie(self.response, "refresh_token")
            
            self.assertEqual(mock_delete.call_count, 2)
            first_call = mock_delete.call_args_list[0]
            second_call = mock_delete.call_args_list[1]
            
            self.assertEqual(first_call[0][0], "access_token")
            self.assertEqual(second_call[0][0], "refresh_token")

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_PATH="/api/v1/",
        JWT_COOKIE_SAMESITE="Strict",
    )
    def test_delete_with_all_custom_settings(self):
        """Verify delete uses all custom settings matching set operation."""
        with patch.object(self.response, "delete_cookie") as mock_delete:
            delete_jwt_cookie(self.response, "access_token")
            
            call_kwargs = mock_delete.call_args[1]
            self.assertEqual(call_kwargs["domain"], ".example.com")
            self.assertEqual(call_kwargs["path"], "/api/v1/")
            self.assertEqual(call_kwargs["samesite"], "Strict")


class CookieUtilityIntegrationTests(TestCase):
    """Integration tests for cookie utilities working together."""

    def setUp(self):
        """Set up test response object."""
        self.response = Response({"status": "ok"})

    def test_set_and_delete_use_consistent_parameters(self):
        """Verify set and delete operations are consistent for cookie lifecycle."""
        with patch.object(self.response, "set_cookie") as mock_set, \
             patch.object(self.response, "delete_cookie") as mock_delete:
            
            token_value = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            max_age = 300
            
            # Simulate setting a cookie during login
            set_jwt_cookie(self.response, "access_token", token_value, max_age)
            
            # Simulate deleting the cookie during logout
            delete_jwt_cookie(self.response, "access_token")
            
            set_kwargs = mock_set.call_args[1]
            delete_kwargs = mock_delete.call_args[1]
            
            # Critical: These parameters must match or cookie won't be deleted
            self.assertEqual(set_kwargs["domain"], delete_kwargs["domain"])
            self.assertEqual(set_kwargs["path"], delete_kwargs["path"])
            self.assertEqual(set_kwargs["samesite"], delete_kwargs["samesite"])

    @override_settings(
        JWT_COOKIE_DOMAIN="localhost",
        JWT_COOKIE_PATH="/",
        JWT_COOKIE_SAMESITE="Lax",
        JWT_COOKIE_SECURE=False,
    )
    def test_development_environment_configuration(self):
        """Verify cookie utilities work with development environment settings."""
        params = get_jwt_cookie_params()
        
        self.assertIsNotNone(params["domain"])
        self.assertFalse(params["secure"])
        self.assertEqual(params["samesite"], "Lax")

    @override_settings(
        JWT_COOKIE_DOMAIN=".example.com",
        JWT_COOKIE_PATH="/",
        JWT_COOKIE_SAMESITE="Lax",
        JWT_COOKIE_SECURE=True,
    )
    def test_production_subdomain_configuration(self):
        """Verify cookie utilities work with production subdomain settings."""
        params = get_jwt_cookie_params()
        
        self.assertEqual(params["domain"], ".example.com")
        self.assertTrue(params["secure"])
        self.assertEqual(params["samesite"], "Lax")
        self.assertTrue(params["httponly"])
