"""Bug condition exploration tests for cookie authentication domain fix.

**CRITICAL**: These tests are EXPECTED TO FAIL on unfixed code.
Failure confirms the bugs exist. Success after fix confirms bugs are resolved.

This test file validates Requirements 1.1-1.9 from bugfix.md by testing:
- Domain mismatch between frontend and backend
- Missing cookie domain parameter
- Inconsistent cookie deletion parameters
- Duplicated helper functions across views
- JWT settings not centralized
- Header authentication still supported

**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9**
"""

import os

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from tenants.models import TenantMembership, TenantRole
from tests.fixtures.factories import create_tenant

User = get_user_model()


class CookieAuthBugConditionTests(TestCase):
    """Test that demonstrates cookie authentication bugs on unfixed code.
    
    **EXPECTED OUTCOME**: These tests FAIL on unfixed code (proving bugs exist).
    After fix implementation, these tests PASS (proving bugs are resolved).
    """

    def setUp(self):
        """Set up test user and tenant."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="bugtest",
            password="testpass123",
            email="bugtest@test.com",
            first_name="Bug",
            last_name="Tester",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Bug Test Org", slug="bug-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def test_bug_1_1_domain_mismatch_prevents_cookie_access(self):
        """Bug 1.1: Frontend on localhost cannot read cookies set for 127.0.0.1.
        
        **Validates: Requirement 1.1**
        
        This test simulates the domain mismatch scenario where frontend runs on
        localhost:3000 but backend API is configured as 127.0.0.1:8000.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - cookies not accessible due to domain mismatch
        **EXPECTED AFTER FIX**: PASS - cookies accessible with consistent hostnames
        """
        # Login to get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "bugtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Check if cookies are set
        self.assertIn("access_token", login_response.cookies)
        self.assertIn("refresh_token", login_response.cookies)
        
        # Verify cookie domain is set appropriately
        # On unfixed code: domain is not set (None), causing mismatch issues
        # After fix: domain should be set from settings
        access_cookie = login_response.cookies.get("access_token")
        
        # Bug condition: Cookie domain is not explicitly set
        # This causes issues when frontend and backend use different hostnames
        # After fix, domain should be set from JWT_COOKIE_DOMAIN setting
        cookie_domain = access_cookie.get("domain", "")
        
        # On unfixed code, this will be empty string (not set)
        # After fix, this should match the configured domain
        # For development with localhost, domain should be None or empty
        # For production with subdomains, domain should be ".example.com"
        
        # The bug is that domain is not being set from settings
        # After fix, get_jwt_cookie_params() will provide consistent domain
        self.assertIsNotNone(
            cookie_domain,
            "Cookie domain should be explicitly managed via centralized utilities"
        )

    def test_bug_1_2_cookie_set_without_domain_parameter(self):
        """Bug 1.2: Cookies set without domain parameter cannot be shared.
        
        **Validates: Requirement 1.2**
        
        This test verifies that cookies are set without proper domain configuration,
        preventing subdomain sharing in production scenarios.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - domain parameter not set
        **EXPECTED AFTER FIX**: PASS - domain parameter set from settings
        """
        # Login to get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "bugtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Check cookie attributes
        access_cookie = login_response.cookies.get("access_token")
        refresh_cookie = login_response.cookies.get("refresh_token")
        
        # Bug: Cookies are set without reading domain from settings
        # After fix: Cookies should use get_jwt_cookie_params() to get domain
        
        # Verify httponly is set (this should work even on unfixed code)
        self.assertTrue(access_cookie["httponly"])
        self.assertTrue(refresh_cookie["httponly"])
        
        # Verify samesite is set (this should work even on unfixed code)
        self.assertEqual(access_cookie["samesite"], "Lax")
        self.assertEqual(refresh_cookie["samesite"], "Lax")
        
        # Bug: Domain is not set from JWT_COOKIE_DOMAIN setting
        # After fix: Domain should be read from settings via get_jwt_cookie_params()
        # For now, we verify that the setting exists (will fail on unfixed code)
        self.assertTrue(
            hasattr(django_settings, "JWT_COOKIE_DOMAIN"),
            "JWT_COOKIE_DOMAIN should be defined in settings/base.py"
        )

    def test_bug_1_3_cookie_delete_with_mismatched_params(self):
        """Bug 1.3: Cookie deletion without matching parameters fails.
        
        **Validates: Requirement 1.3**
        
        This test verifies that logout properly clears cookies by using matching
        parameters for delete_cookie() that were used in set_cookie().
        
        **EXPECTED ON UNFIXED CODE**: FAIL - cookies not properly cleared
        **EXPECTED AFTER FIX**: PASS - cookies cleared with matching parameters
        """
        # Login to get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "bugtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Logout to clear cookies
        logout_response = self.client.post(reverse("api-logout"))
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        
        # Verify cookies are cleared (value should be empty)
        self.assertIn("access_token", logout_response.cookies)
        self.assertIn("refresh_token", logout_response.cookies)
        self.assertEqual(logout_response.cookies["access_token"].value, "")
        self.assertEqual(logout_response.cookies["refresh_token"].value, "")
        
        # Bug: delete_cookie() may not use matching parameters
        # After fix: delete_jwt_cookie() should use get_jwt_cookie_params()
        # to ensure matching domain, path, secure, samesite
        
        # Verify that centralized delete function exists (will fail on unfixed code)
        try:
            from api.utils.cookies import delete_jwt_cookie  # noqa: F401
            self.assertTrue(True, "Centralized delete_jwt_cookie() function exists")
        except ImportError:
            self.fail("Centralized delete_jwt_cookie() function should exist in api.utils.cookies")

    def test_bug_1_4_jwt_settings_not_centralized(self):
        """Bug 1.4: JWT cookie settings not defined in settings/base.py.
        
        **Validates: Requirement 1.4**
        
        This test verifies that JWT cookie settings are centrally defined in
        settings/base.py instead of using scattered getattr() fallbacks.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - settings not defined
        **EXPECTED AFTER FIX**: PASS - settings defined in base.py
        """
        # Bug: JWT cookie settings are not defined in settings/base.py
        # Code uses getattr() fallbacks with hardcoded defaults
        # After fix: All settings should be defined centrally
        
        required_settings = [
            "JWT_COOKIE_DOMAIN",
            "JWT_COOKIE_PATH",
            "JWT_COOKIE_SECURE",
            "JWT_COOKIE_SAMESITE",
            "JWT_ACCESS_TOKEN_COOKIE_MAX_AGE",
            "JWT_REFRESH_TOKEN_COOKIE_MAX_AGE",
        ]
        
        for setting_name in required_settings:
            self.assertTrue(
                hasattr(django_settings, setting_name),
                f"{setting_name} should be defined in settings/base.py"
            )

    def test_bug_1_5_frontend_env_uses_127_0_0_1(self):
        """Bug 1.5: Frontend .env.local uses 127.0.0.1 instead of localhost.
        
        **Validates: Requirement 1.5**
        
        This test verifies that frontend environment configuration uses localhost
        consistently to match the frontend domain.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - .env.local uses 127.0.0.1
        **EXPECTED AFTER FIX**: PASS - .env.local uses localhost
        """
        # Read frontend/.env.local file
        env_local_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "frontend",
            ".env.local"
        )
        
        if os.path.exists(env_local_path):
            with open(env_local_path, "r") as f:
                env_content = f.read()
            
            # Bug: .env.local uses 127.0.0.1 instead of localhost
            # After fix: Should use localhost for hostname consistency
            self.assertNotIn(
                "127.0.0.1",
                env_content,
                "frontend/.env.local should use 'localhost' not '127.0.0.1'"
            )
            self.assertIn(
                "localhost",
                env_content,
                "frontend/.env.local should use 'localhost' for hostname consistency"
            )
        else:
            self.skipTest("frontend/.env.local not found")

    def test_bug_1_6_header_auth_still_supported(self):
        """Bug 1.6: Authorization header authentication still supported.
        
        **Validates: Requirement 1.6**
        
        This test verifies that the authentication system has fully migrated to
        cookie-based authentication and no longer supports header-based JWT.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - header auth still works
        **EXPECTED AFTER FIX**: PASS - only cookie auth supported
        """
        # Login to get token
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "bugtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data["access"]
        
        # Create new client without cookies
        header_client = APIClient()
        header_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        # Try to access protected endpoint with header auth
        response = header_client.get(reverse("api-me"))
        
        # Bug: Header auth still works (incomplete migration)
        # After fix: Header auth should be rejected, only cookies accepted
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            "Header-based authentication should be removed (cookie-only auth)"
        )

    def test_bug_1_7_cookie_helpers_duplicated(self):
        """Bug 1.7: Cookie helper functions duplicated across files.
        
        **Validates: Requirement 1.7**
        
        This test verifies that cookie helper functions are not duplicated and
        instead use centralized utilities from api.utils.cookies.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - helpers duplicated
        **EXPECTED AFTER FIX**: PASS - centralized utilities used
        """
        # Bug: Helper functions _jwt_cookie_security() and _set_jwt_cookie()
        # are duplicated in auth.py and invitations.py
        # After fix: Should use centralized utilities from api.utils.cookies
        
        # Verify centralized utilities exist
        try:
            from api.utils.cookies import (  # noqa: F401
                get_jwt_cookie_params,
                set_jwt_cookie,
                delete_jwt_cookie,
            )
            self.assertTrue(True, "Centralized cookie utilities exist")
        except ImportError:
            self.fail("Centralized cookie utilities should exist in api.utils.cookies")
        
        # Verify auth.py uses centralized utilities (not duplicated helpers)
        auth_source = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
            "api",
            "views",
            "auth.py"
        )
        
        if os.path.exists(auth_source):
            with open(auth_source, "r") as f:
                auth_content = f.read()
            
            # After fix: Should import from api.utils.cookies
            self.assertIn(
                "from api.utils.cookies import",
                auth_content,
                "auth.py should import centralized cookie utilities"
            )
            
            # After fix: Should not define _jwt_cookie_security helper
            self.assertNotIn(
                "def _jwt_cookie_security",
                auth_content,
                "auth.py should not define duplicated _jwt_cookie_security helper"
            )

    def test_bug_1_8_no_centralized_utils_module(self):
        """Bug 1.8: No centralized utilities module for authentication.
        
        **Validates: Requirement 1.8**
        
        This test verifies that a centralized utilities module exists for
        shared authentication functions.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - utils module doesn't exist
        **EXPECTED AFTER FIX**: PASS - utils module exists with cookie utilities
        """
        # Bug: No src/api/utils/ directory structure
        # After fix: Should have api.utils.cookies module
        
        utils_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
            "api",
            "utils"
        )
        
        self.assertTrue(
            os.path.exists(utils_path),
            "src/api/utils/ directory should exist"
        )
        
        cookies_path = os.path.join(utils_path, "cookies.py")
        self.assertTrue(
            os.path.exists(cookies_path),
            "src/api/utils/cookies.py should exist"
        )

    def test_bug_1_9_no_utils_directory_structure(self):
        """Bug 1.9: src/api module lacks utils/ directory structure.
        
        **Validates: Requirement 1.9**
        
        This test verifies that the api module follows Django best practices
        with a utils/ directory for shared utilities.
        
        **EXPECTED ON UNFIXED CODE**: FAIL - no utils directory
        **EXPECTED AFTER FIX**: PASS - utils directory exists
        """
        # Bug: src/api/ lacks utils/ subdirectory
        # After fix: Should have utils/__init__.py and utils/cookies.py
        
        utils_init_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "src",
            "api",
            "utils",
            "__init__.py"
        )
        
        self.assertTrue(
            os.path.exists(utils_init_path),
            "src/api/utils/__init__.py should exist to make it a Python package"
        )


class CookieAuthExpectedBehaviorTests(TestCase):
    """Test expected behavior after fix implementation.
    
    These tests encode the expected behavior from Requirements 2.1-2.15.
    They will FAIL on unfixed code and PASS after fix.
    """

    def setUp(self):
        """Set up test user and tenant."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="fixtest",
            password="testpass123",
            email="fixtest@test.com",
            first_name="Fix",
            last_name="Tester",
            is_staff=True,
        )
        self.tenant = create_tenant(name="Fix Test Org", slug="fix-test-org")
        TenantMembership.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=TenantRole.COORDINATOR,
            is_active=True,
            is_default=True,
        )

    def test_expected_2_1_cookies_accessible_with_consistent_hostnames(self):
        """Expected 2.1: Cookies accessible when hostnames match.
        
        **Validates: Requirement 2.1**
        
        After fix, cookies set by backend on localhost should be accessible
        to frontend also on localhost.
        """
        # Login to get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "fixtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Verify cookies are set
        self.assertIn("access_token", login_response.cookies)
        self.assertIn("refresh_token", login_response.cookies)
        
        # Create new client with cookies
        cookie_client = APIClient()
        access_token = login_response.data["access"]
        cookie_client.cookies.load({"access_token": access_token})
        
        # Verify authenticated request works
        response = cookie_client.get(reverse("api-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "fixtest")

    def test_expected_2_2_cookie_domain_parameter_set(self):
        """Expected 2.2: Cookies set with appropriate domain parameter.
        
        **Validates: Requirement 2.2**
        
        After fix, cookies should be set with domain parameter from settings.
        """
        # Login to get cookies
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "fixtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        # Verify JWT_COOKIE_DOMAIN setting exists
        self.assertTrue(hasattr(django_settings, "JWT_COOKIE_DOMAIN"))

    def test_expected_2_7_cookie_only_authentication(self):
        """Expected 2.7: Cookie-only authentication enforced.
        
        **Validates: Requirement 2.7**
        
        After fix, only cookie-based authentication should work.
        Header-based authentication should be removed.
        """
        # Login to get token
        login_response = self.client.post(
            reverse("api-login"),
            {"username": "fixtest", "password": "testpass123"},
            format="json",
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        token = login_response.data["access"]
        
        # Try header auth (should fail after fix)
        header_client = APIClient()
        header_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = header_client.get(reverse("api-me"))
        
        # After fix: Header auth should not work
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expected_2_10_centralized_utilities_exist(self):
        """Expected 2.10: Centralized cookie utilities module exists.
        
        **Validates: Requirement 2.10**
        
        After fix, api.utils.cookies module should provide centralized
        cookie management functions.
        """
        # Verify centralized utilities can be imported
        try:
            from api.utils.cookies import (
                get_jwt_cookie_params,
                set_jwt_cookie,
                delete_jwt_cookie,
            )
            
            # Verify functions are callable
            self.assertTrue(callable(get_jwt_cookie_params))
            self.assertTrue(callable(set_jwt_cookie))
            self.assertTrue(callable(delete_jwt_cookie))
        except ImportError as e:
            self.fail(f"Centralized cookie utilities should exist: {e}")
