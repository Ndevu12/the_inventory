# Implementation Plan

## Phase 1: Exploration Tests (BEFORE Fix)

- [ ] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Cookie Authentication Domain Mismatch
  - **CRITICAL**: This test MUST FAIL on unfixed code - failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior - it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the bugs exist
  - **Scoped PBT Approach**: Test concrete failing scenarios: domain mismatch (localhost vs 127.0.0.1), missing cookie domain parameter, inconsistent cookie deletion parameters, duplicated helper functions, and header auth still supported
  - Test implementation details from Bug Condition in design:
    - Frontend on `localhost:3000` with backend on `127.0.0.1:8000` prevents cookie sharing
    - Cookies set without domain parameter cannot be shared across subdomains
    - Cookie deletion without matching parameters fails to clear cookies
    - Helper functions `_jwt_cookie_security()` and `_set_jwt_cookie()` are duplicated in multiple files
    - JWT settings are not centralized in `settings/base.py`
    - Authorization header authentication is still supported
  - The test assertions should match the Expected Behavior Properties from design:
    - Cookies should be accessible when frontend and backend use consistent hostnames
    - Centralized utilities should provide consistent cookie management
    - Cookie-only authentication should be enforced
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS (this is correct - it proves the bugs exist)
  - Document counterexamples found to understand root causes:
    - Cookies not accessible due to domain mismatch
    - Cookies not properly cleared on logout
    - Settings scattered with `getattr()` fallbacks
    - Code duplication across views
    - Header auth still functional
  - Mark task complete when test is written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9_

- [ ] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Cookie Authentication Behavior
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-cookie operations:
    - JWT token generation (signing, claims, expiration)
    - User authentication logic (password validation, user lookup)
    - Tenant membership resolution and role checking
    - Non-authentication API endpoints (inventory, sales, reports)
    - Wagtail admin session-based authentication
    - CORS settings for cross-origin requests
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - JWT token generation produces consistent tokens
    - User authentication validates credentials correctly
    - Tenant membership checking returns correct roles
    - API endpoints process requests correctly
    - Wagtail admin authentication works independently
    - CORS allows credentials for cross-origin requests
  - Property-based testing generates many test cases for stronger guarantees
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7_

## Phase 2: Implementation

- [ ] 3. Fix cookie authentication domain issues and centralize utilities

  - [ ] 3.1 Create centralized cookie utilities module
    - Create `src/api/utils/__init__.py` (empty file to make it a Python package)
    - Create `src/api/utils/cookies.py` with three core functions:
      - `get_jwt_cookie_params()`: Returns dict of cookie parameters from Django settings with defaults (domain, path, secure, samesite, httponly)
      - `set_jwt_cookie(response, key, value, max_age)`: Sets JWT cookie with consistent parameters
      - `delete_jwt_cookie(response, key)`: Deletes JWT cookie with matching parameters
    - Add comprehensive docstrings documenting purpose, parameters, return values, and usage examples
    - Ensure functions read from Django settings (JWT_COOKIE_DOMAIN, JWT_COOKIE_PATH, JWT_COOKIE_SECURE, JWT_COOKIE_SAMESITE)
    - _Bug_Condition: cookieHelpersAreDuplicated(input.codebase) AND NOT hasCentralizedUtilities(input.codebase)_
    - _Expected_Behavior: Centralized utilities provide consistent cookie management (Property 2 from design)_
    - _Preservation: JWT token generation and validation logic unchanged_
    - _Requirements: 2.10, 2.11, 2.12, 2.13, 2.14, 2.15_

  - [ ] 3.2 Add JWT cookie settings to Django configuration
    - Add JWT cookie settings section to `src/the_inventory/settings/base.py` after SIMPLE_JWT configuration:
      - JWT_COOKIE_DOMAIN (default: None)
      - JWT_COOKIE_PATH (default: "/")
      - JWT_COOKIE_SAMESITE (default: "Lax")
      - JWT_COOKIE_SECURE (default: not DEBUG)
      - JWT_ACCESS_TOKEN_COOKIE_MAX_AGE (default: 300 seconds)
      - JWT_REFRESH_TOKEN_COOKIE_MAX_AGE (default: 604800 seconds)
    - Add comments explaining cookie domain behavior (None vs ".example.com" vs "localhost")
    - Update `src/the_inventory/settings/production.py` to remove JWT_COOKIE_SECURE override (now handled by base.py)
    - _Bug_Condition: jwtSettingsNotCentralized(input.settings)_
    - _Expected_Behavior: Settings defined centrally with appropriate defaults (Property 1 from design)_
    - _Preservation: Existing Django settings and configuration unchanged_
    - _Requirements: 2.4_

  - [ ] 3.3 Remove header-based authentication support
    - Update `src/api/authentication.py`:
      - Update class docstring to remove references to "header-based JWT" and "Authorization: Bearer"
      - Simplify `authenticate()` method to read from cookies only (remove `super().authenticate(request)` call)
      - Only read `access_token` from `request.COOKIES`, return None if not found
      - Update module docstring to remove references to header precedence
    - _Bug_Condition: headerAuthStillSupported(input.authBackend)_
    - _Expected_Behavior: Cookie-only authentication enforced (Property 3 from design)_
    - _Preservation: JWT token validation logic unchanged_
    - _Requirements: 2.7, 2.8, 2.9_

  - [ ] 3.4 Refactor authentication views to use centralized utilities
    - Update `src/api/views/auth.py`:
      - Add import: `from api.utils.cookies import delete_jwt_cookie, set_jwt_cookie`
      - Update `LoginView.post()`: Replace inline cookie setting with `set_jwt_cookie()` calls for access_token and refresh_token
      - Update `RefreshView.post()`: Replace inline cookie setting with `set_jwt_cookie()` call for access_token
      - Update `LogoutView.post()`: Replace inline cookie deletion with `delete_jwt_cookie()` calls
      - Remove all `getattr()` fallbacks, use direct settings access
    - Update `src/api/views/invitations.py`:
      - Remove helper functions `_jwt_cookie_security()` and `_set_jwt_cookie()` (lines 55-67)
      - Add import: `from api.utils.cookies import set_jwt_cookie`
      - Update `AcceptInvitationView.post()`: Replace `_set_jwt_cookie()` calls with centralized `set_jwt_cookie()` calls
      - Remove all `getattr()` fallbacks, use direct settings access
    - _Bug_Condition: cookieHelpersAreDuplicated(input.codebase) AND cookieSetWithoutDomain(input) AND cookieDeleteWithMismatchedParams(input)_
    - _Expected_Behavior: All views use centralized utilities with consistent parameters (Property 2 from design)_
    - _Preservation: Authentication flow logic and response data unchanged_
    - _Requirements: 2.10, 2.11, 2.13, 2.14, 3.7_

  - [ ] 3.5 Update environment configuration files
    - Update `frontend/.env.local`:
      - Change NEXT_PUBLIC_API_URL from `http://127.0.0.1:8000/api/v1` to `http://localhost:8000/api/v1`
    - Update `frontend/.env.example`:
      - Add comment emphasizing hostname consistency (use 'localhost', not '127.0.0.1')
      - Add note about cookie-based authentication requiring same hostname
    - Update `.env.example`:
      - Add new "JWT COOKIE CONFIGURATION" section with all JWT cookie environment variables
      - Document JWT_COOKIE_DOMAIN, JWT_COOKIE_PATH, JWT_COOKIE_SAMESITE, JWT_COOKIE_SECURE, JWT_ACCESS_TOKEN_COOKIE_MAX_AGE, JWT_REFRESH_TOKEN_COOKIE_MAX_AGE
      - Provide examples for development (localhost) and production (.example.com) scenarios
      - Update DEPLOYMENT NOTES to mention hostname consistency requirement
    - _Bug_Condition: input.frontendHost == "localhost" AND input.backendHost == "127.0.0.1"_
    - _Expected_Behavior: Frontend and backend use consistent hostnames (Property 1 from design)_
    - _Preservation: Other environment variables unchanged_
    - _Requirements: 2.5, 2.6_

  - [ ] 3.6 Update documentation
    - Update `docs/ENVIRONMENT.md`:
      - Add new section "JWT Cookie Configuration" explaining cookie domain behavior
      - Document all JWT cookie environment variables with examples
      - Update "Development Setup" section to emphasize hostname consistency (use localhost, not 127.0.0.1)
      - Update "Production Deployment" section to include JWT cookie configuration in checklist
      - Provide example for subdomain cookie sharing with JWT_COOKIE_DOMAIN=".example.com"
    - _Bug_Condition: Documentation does not explain cookie domain configuration_
    - _Expected_Behavior: Comprehensive documentation for JWT cookie setup_
    - _Preservation: Existing documentation sections unchanged_
    - _Requirements: 2.6_

  - [ ] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Cookie Authentication Works Correctly
    - **IMPORTANT**: Re-run the SAME test from task 1 - do NOT write a new test
    - The test from task 1 encodes the expected behavior
    - When this test passes, it confirms the expected behavior is satisfied:
      - Cookies are accessible when frontend and backend use consistent hostnames
      - Centralized utilities provide consistent cookie management
      - Cookie-only authentication is enforced
      - Settings are centralized in base.py
      - Code duplication is eliminated
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES (confirms bugs are fixed)
    - _Requirements: Expected Behavior Properties from design (2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10, 2.11, 2.12, 2.13, 2.14, 2.15)_

  - [ ] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Cookie Operations Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 - do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS (confirms no regressions)
    - Confirm all tests still pass after fix:
      - JWT token generation produces identical tokens
      - User authentication validates credentials correctly
      - Tenant membership checking returns correct roles
      - API endpoints process requests correctly
      - Wagtail admin authentication works independently
      - CORS allows credentials for cross-origin requests
    - _Requirements: Preservation Requirements from design (3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7)_

## Phase 3: Testing & Validation

- [ ] 4. Write unit tests for centralized cookie utilities
  - Test `get_jwt_cookie_params()` returns correct parameters from settings with proper defaults
  - Test `set_jwt_cookie()` calls `response.set_cookie()` with all required parameters (domain, path, secure, samesite, httponly, max_age)
  - Test `delete_jwt_cookie()` calls `response.delete_cookie()` with matching parameters (domain, path, secure, samesite)
  - Mock Django settings to test different configurations (DEBUG=True/False, custom domain, custom path)
  - _Requirements: 2.10, 2.13, 2.15_

- [ ] 5. Write unit tests for authentication backend
  - Test `CookieJWTAuthentication.authenticate()` reads from cookies only (not headers)
  - Test authentication returns None when access_token cookie is missing
  - Test authentication returns (user, token) when valid access_token cookie is present
  - Test authentication raises InvalidToken when invalid access_token cookie is present
  - Test that Authorization header is ignored (no longer supported)
  - _Requirements: 2.7, 2.8, 2.9_

- [ ] 6. Write unit tests for authentication views
  - Test `LoginView.post()` sets both access_token and refresh_token cookies with correct max_age
  - Test `RefreshView.post()` sets new access_token cookie with correct max_age
  - Test `LogoutView.post()` deletes both access_token and refresh_token cookies
  - Test `AcceptInvitationView.post()` sets both cookies with correct max_age
  - Mock `set_jwt_cookie()` and `delete_jwt_cookie()` to verify they are called with correct parameters
  - _Requirements: 2.10, 2.11, 2.14_

- [ ] 7. Write integration tests for full authentication flows
  - Test full login flow: POST to /auth/login/, verify cookies are set in response, verify subsequent requests are authenticated
  - Test full refresh flow: POST to /auth/refresh/ with refresh_token cookie, verify new access_token cookie is set
  - Test full logout flow: POST to /auth/logout/, verify cookies are deleted, verify subsequent requests are unauthenticated
  - Test invitation accept flow: POST to /auth/invitations/<token>/accept/, verify cookies are set, verify user is authenticated
  - Test that requests with Authorization header are NOT authenticated (header auth removed)
  - _Requirements: 2.1, 2.7, 2.8, 3.1_

- [ ] 8. Write integration tests for cross-origin and subdomain scenarios
  - Test cross-origin requests with CORS and credentials, verify cookies are sent and authentication works
  - Test production subdomain scenario with JWT_COOKIE_DOMAIN=".example.com", verify cookies are shared across subdomains (api.example.com and app.example.com)
  - Test development scenario with JWT_COOKIE_DOMAIN=None, verify cookies work for exact hostname match
  - _Requirements: 2.2, 3.2, 3.4_

- [ ] 9. Update existing authentication tests
  - Update tests that use Authorization header to use cookie-based authentication instead
  - Ensure all existing authentication tests pass with cookie-based approach
  - Remove tests that specifically validate header-based authentication (no longer supported)
  - _Requirements: 3.1, 3.6_

## Phase 4: Checkpoint

- [ ] 10. Checkpoint - Ensure all tests pass
  - Run full test suite: `python manage.py test`
  - Run frontend tests: `cd frontend && yarn test`
  - Verify no regressions in existing functionality
  - Verify all new tests pass
  - Verify bug condition exploration test passes (confirms fix works)
  - Verify preservation tests pass (confirms no regressions)
  - Ask the user if questions arise or if manual testing is needed
  - _Requirements: All requirements (1.1-3.7)_
