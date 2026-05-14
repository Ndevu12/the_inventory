# Cookie-Based Authentication Domain Fix - Technical Design

## Overview

This design addresses the incomplete migration to cookie-based JWT authentication by fixing domain mismatch issues, centralizing cookie management utilities, removing header-based authentication support, and establishing proper configuration management. The fix ensures cookies work correctly in both development (localhost) and production (subdomain) scenarios while eliminating code duplication and inconsistent implementations across the authentication system.

The approach involves creating a centralized cookie utility module, adding proper Django settings for JWT cookies, updating environment configuration files for hostname consistency, removing Authorization header support from the authentication backend, and refactoring all authentication views to use the centralized utilities.

## Glossary

- **Bug_Condition (C)**: The condition that triggers authentication failures - when frontend and backend use different hostnames (localhost vs 127.0.0.1) or when cookie parameters are inconsistent across views
- **Property (P)**: The desired behavior - cookies set by the backend are accessible to the frontend, enabling successful authentication with consistent parameters
- **Preservation**: Existing authentication flows, CORS settings, and Wagtail admin authentication that must remain unchanged
- **CookieJWTAuthentication**: The authentication class in `src/api/authentication.py` that validates JWT tokens from cookies or headers
- **JWTAuthMiddleware**: The middleware in `src/api/middleware.py` that runs authentication early in the request cycle
- **Domain Mismatch**: Browser security restriction where cookies set for `127.0.0.1` cannot be read by `localhost` (treated as different domains)
- **Cookie Parameters**: The set of attributes (domain, path, secure, samesite, httponly, max_age) that must match between set_cookie() and delete_cookie() calls
- **Centralized Utilities**: Reusable functions in `src/api/utils/cookies.py` that provide consistent cookie management across all views

## Bug Details

### Bug Condition

The bug manifests when the frontend runs on `localhost:3000` while the backend API is configured as `127.0.0.1:8000`, or when cookie setting/deletion operations use inconsistent parameters across different views. The authentication system fails because browsers treat `localhost` and `127.0.0.1` as different domains, preventing cookie sharing. Additionally, duplicated cookie helper functions across multiple files lead to inconsistent implementations and maintenance issues.

**Formal Specification:**
```
FUNCTION isBugCondition(input)
  INPUT: input of type AuthenticationRequest
  OUTPUT: boolean
  
  RETURN (input.frontendHost == "localhost" AND input.backendHost == "127.0.0.1")
         OR (cookieSetWithoutDomain(input))
         OR (cookieDeleteWithMismatchedParams(input))
         OR (cookieHelpersAreDuplicated(input.codebase))
         OR (jwtSettingsNotCentralized(input.settings))
         OR (headerAuthStillSupported(input.authBackend))
END FUNCTION
```

### Examples

- **Domain Mismatch**: Frontend on `http://localhost:3000` calls backend at `http://127.0.0.1:8000/api/v1/auth/login/`. Backend sets cookies for `127.0.0.1`, but frontend cannot read them because browser treats `localhost` as a different domain. Authentication fails.

- **Missing Domain Parameter**: Backend calls `response.set_cookie('access_token', value, httponly=True)` without specifying `domain` parameter. Cookie is bound to exact request domain and cannot be shared across subdomains in production (e.g., `api.example.com` vs `app.example.com`).

- **Inconsistent Cookie Deletion**: Login view sets cookie with `domain=None, path='/', secure=True, samesite='Lax'`, but logout view calls `delete_cookie('access_token', samesite='Lax')` without matching `domain`, `path`, and `secure` parameters. Cookie is not properly cleared from browser.

- **Duplicated Helper Functions**: `src/api/views/auth.py` defines `_jwt_cookie_security()` helper (lines 49-51) and `src/api/views/invitations.py` defines identical `_jwt_cookie_security()` helper (lines 55-58). When cookie security logic needs to change, developers must update both locations, leading to inconsistency and bugs.

- **Scattered Settings**: Code uses `getattr(django_settings, 'JWT_COOKIE_SECURE', not django_settings.DEBUG)` in multiple places with different fallback logic. No single source of truth for JWT cookie configuration.

- **Header Auth Still Supported**: `CookieJWTAuthentication.authenticate()` checks Authorization header first, then falls back to cookies. This contradicts the goal of full migration to cookie-based authentication and creates confusion about the primary authentication method.

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Existing tests for authentication endpoints must continue to pass (with modifications to use cookie-based authentication)
- Production deployments with proper subdomain configuration must continue to work
- Django session cookies for Wagtail admin authentication must function independently
- CORS settings allowing credentials must continue to support cross-origin authenticated requests
- JWT token generation and validation logic must remain unchanged
- User registration, password change, and profile endpoints must continue to work

**Scope:**
All inputs that do NOT involve cookie operations (setting, deleting, reading JWT cookies) should be completely unaffected by this fix. This includes:
- JWT token generation and signing logic
- User authentication and authorization logic
- Tenant membership and role checking
- API endpoint business logic
- Database queries and ORM operations
- Email sending and invitation flows (except cookie setting in accept endpoint)

## Hypothesized Root Cause

Based on the bug description and code analysis, the most likely issues are:

1. **Environment Configuration Mismatch**: The `frontend/.env.local` file uses `127.0.0.1` instead of `localhost`, creating a domain mismatch with the frontend's actual hostname. This is a simple configuration error that prevents cookie sharing.

2. **Missing Cookie Domain Configuration**: The backend sets cookies without specifying a `domain` parameter, relying on browser defaults. This works for exact hostname matches but fails for subdomain scenarios in production and hostname variations in development.

3. **Incomplete Settings Migration**: JWT cookie settings like `JWT_COOKIE_DOMAIN`, `JWT_COOKIE_SECURE`, `JWT_COOKIE_SAMESITE`, `JWT_COOKIE_PATH`, `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`, and `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE` are referenced in code using `getattr()` fallbacks but never defined in `settings/base.py`. This leads to scattered defaults and inconsistent behavior.

4. **Cookie Parameter Mismatch**: The `delete_cookie()` calls in logout views do not match the parameters used in `set_cookie()` calls during login. Browsers require exact parameter matching to delete cookies, so mismatched parameters leave cookies in the browser.

5. **Code Duplication**: Cookie helper functions (`_jwt_cookie_security()`, `_set_jwt_cookie()`) are duplicated across `src/api/views/auth.py` and `src/api/views/invitations.py`. This violates DRY principles and makes maintenance difficult.

6. **Lack of Centralized Utilities**: The `src/api` module lacks a `utils/` directory structure for shared utilities. Cookie management logic is scattered across views instead of being centralized in a reusable module.

7. **Incomplete Authentication Migration**: The `CookieJWTAuthentication` class still supports Authorization header-based authentication as the primary method, with cookies as a fallback. This contradicts the goal of full migration to cookie-based authentication.

## Correctness Properties

Property 1: Bug Condition - Cookie-Based Authentication Works Across Hostname Configurations

_For any_ authentication request where the frontend and backend use consistent hostnames (both `localhost` or both use the same domain), and cookies are set with proper domain parameters, the fixed authentication system SHALL successfully set cookies that are accessible to the frontend, enabling login, token refresh, and logout flows to work correctly.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5, 2.6**

Property 2: Bug Condition - Centralized Cookie Utilities Ensure Consistency

_For any_ cookie operation (setting, deleting, reading) performed by authentication views or invitation views, the fixed system SHALL use centralized utility functions from `src/api/utils/cookies.py` that retrieve parameters from Django settings, ensuring consistent cookie management across the entire authentication system.

**Validates: Requirements 2.10, 2.11, 2.12, 2.13, 2.14, 2.15**

Property 3: Bug Condition - Cookie-Only Authentication

_For any_ authentication request to the API, the fixed authentication backend SHALL read JWT tokens exclusively from cookies, removing support for Authorization header-based authentication, ensuring consistency with the cookie-based authentication approach.

**Validates: Requirements 2.7, 2.8, 2.9**

Property 4: Preservation - Existing Functionality Unchanged

_For any_ authentication flow that does NOT involve cookie operations (token generation, user validation, tenant membership checking), the fixed system SHALL produce exactly the same behavior as the original system, preserving all existing functionality for JWT token logic, user authentication, and API business logic.

**Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7**

## Fix Implementation

### Changes Required

Assuming our root cause analysis is correct, the following changes are required:

#### 1. Create Centralized Cookie Utilities Module

**File**: `src/api/utils/__init__.py` (new file)

**Purpose**: Initialize the utils package

**Specific Changes**:
1. Create empty `__init__.py` file to make `src/api/utils/` a Python package

---

**File**: `src/api/utils/cookies.py` (new file)

**Purpose**: Centralized cookie management utilities for JWT authentication

**Specific Changes**:
1. **Create `get_jwt_cookie_params()` function**: Returns a dictionary of cookie parameters read from Django settings with appropriate defaults
   - Read `JWT_COOKIE_DOMAIN` from settings (default: `None`)
   - Read `JWT_COOKIE_PATH` from settings (default: `'/'`)
   - Read `JWT_COOKIE_SECURE` from settings (default: `not DEBUG`)
   - Read `JWT_COOKIE_SAMESITE` from settings (default: `'Lax'`)
   - Return dict with keys: `domain`, `path`, `secure`, `samesite`, `httponly` (always `True`)

2. **Create `set_jwt_cookie()` function**: Sets a JWT cookie with consistent parameters
   - Parameters: `response`, `key`, `value`, `max_age`
   - Call `get_jwt_cookie_params()` to get cookie parameters
   - Call `response.set_cookie()` with all parameters including `httponly=True`

3. **Create `delete_jwt_cookie()` function**: Deletes a JWT cookie with matching parameters
   - Parameters: `response`, `key`
   - Call `get_jwt_cookie_params()` to get cookie parameters
   - Call `response.delete_cookie()` with matching `domain`, `path`, `secure`, `samesite` parameters

4. **Add comprehensive docstrings**: Document each function with purpose, parameters, return values, and usage examples

---

#### 2. Add JWT Cookie Settings to Django Configuration

**File**: `src/the_inventory/settings/base.py`

**Purpose**: Define centralized JWT cookie configuration

**Specific Changes**:
1. **Add JWT cookie settings section** (after SIMPLE_JWT configuration, around line 350):
   ```python
   # JWT Cookie Configuration
   JWT_COOKIE_DOMAIN = env_str("JWT_COOKIE_DOMAIN", None)
   JWT_COOKIE_PATH = env_str("JWT_COOKIE_PATH", "/") or "/"
   JWT_COOKIE_SAMESITE = env_str("JWT_COOKIE_SAMESITE", "Lax") or "Lax"
   JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", not DEBUG)
   JWT_ACCESS_TOKEN_COOKIE_MAX_AGE = env_int("JWT_ACCESS_TOKEN_COOKIE_MAX_AGE", 300)
   JWT_REFRESH_TOKEN_COOKIE_MAX_AGE = env_int("JWT_REFRESH_TOKEN_COOKIE_MAX_AGE", 604800)
   ```

2. **Add comment explaining cookie domain behavior**:
   - `None` (default) = cookie bound to exact request domain
   - `".example.com"` (with leading dot) = cookie shared across all subdomains
   - `"localhost"` = cookie for localhost only (development)

---

**File**: `src/the_inventory/settings/production.py`

**Purpose**: Override JWT_COOKIE_SECURE for production

**Specific Changes**:
1. **Remove existing JWT_COOKIE_SECURE override** (line 115): This is now handled by base.py with proper defaults
2. **Add comment**: JWT cookie settings are configured in base.py with environment variable overrides

---

#### 3. Remove Header-Based Authentication Support

**File**: `src/api/authentication.py`

**Purpose**: Remove Authorization header support, use cookies exclusively

**Specific Changes**:
1. **Update class docstring**: Remove references to "header-based JWT" and "Authorization: Bearer". Document that this class reads JWT tokens from cookies only.

2. **Simplify `authenticate()` method**: Remove the `super().authenticate(request)` call that checks Authorization headers. Only read from cookies:
   ```python
   def authenticate(self, request):
       """Authenticate request using cookie only.
       
       Returns:
           tuple (user, auth_token) if authenticated, None if no token found
           
       Raises:
           InvalidToken: if token is present but invalid
       """
       access_token = request.COOKIES.get('access_token')
       if access_token is None:
           return None
       
       try:
           validated_token = self.get_validated_token(access_token)
           user = self.get_user(validated_token)
           return (user, validated_token)
       except InvalidToken:
           return None
   ```

3. **Update module docstring**: Remove references to "both header-based JWT and HttpOnly cookie-based JWT" and "Header takes precedence over cookie"

---

#### 4. Refactor Authentication Views to Use Centralized Utilities

**File**: `src/api/views/auth.py`

**Purpose**: Remove duplicated helpers, use centralized cookie utilities

**Specific Changes**:
1. **Add import at top of file**:
   ```python
   from api.utils.cookies import delete_jwt_cookie, set_jwt_cookie
   ```

2. **Update `LoginView.post()` method** (lines 49-68):
   - Remove inline cookie setting logic
   - Replace with calls to `set_jwt_cookie()`:
     ```python
     if access_token and refresh_token:
         set_jwt_cookie(
             response=response,
             key='access_token',
             value=access_token,
             max_age=django_settings.JWT_ACCESS_TOKEN_COOKIE_MAX_AGE,
         )
         set_jwt_cookie(
             response=response,
             key='refresh_token',
             value=refresh_token,
             max_age=django_settings.JWT_REFRESH_TOKEN_COOKIE_MAX_AGE,
         )
     ```

3. **Update `RefreshView.post()` method** (lines 104-112):
   - Remove inline cookie setting logic
   - Replace with call to `set_jwt_cookie()`:
     ```python
     if access_token:
         set_jwt_cookie(
             response=response,
             key='access_token',
             value=access_token,
             max_age=django_settings.JWT_ACCESS_TOKEN_COOKIE_MAX_AGE,
         )
     ```

4. **Update `LogoutView.post()` method** (lines 134-143):
   - Remove inline cookie deletion logic
   - Replace with calls to `delete_jwt_cookie()`:
     ```python
     delete_jwt_cookie(response, 'access_token')
     delete_jwt_cookie(response, 'refresh_token')
     ```

5. **Remove all references to `getattr()` fallbacks**: Use direct settings access since settings are now defined in base.py

---

**File**: `src/api/views/invitations.py`

**Purpose**: Remove duplicated helpers, use centralized cookie utilities

**Specific Changes**:
1. **Remove helper functions** (lines 55-67):
   - Delete `_jwt_cookie_security()` function
   - Delete `_set_jwt_cookie()` function

2. **Add import at top of file**:
   ```python
   from api.utils.cookies import set_jwt_cookie
   ```

3. **Update `AcceptInvitationView.post()` method** (lines 234-247):
   - Remove calls to `_set_jwt_cookie()` helper
   - Replace with calls to centralized `set_jwt_cookie()`:
     ```python
     set_jwt_cookie(
         response=response,
         key='access_token',
         value=str(refresh.access_token),
         max_age=django_settings.JWT_ACCESS_TOKEN_COOKIE_MAX_AGE,
     )
     set_jwt_cookie(
         response=response,
         key='refresh_token',
         value=str(refresh),
         max_age=django_settings.JWT_REFRESH_TOKEN_COOKIE_MAX_AGE,
     )
     ```

4. **Remove all references to `getattr()` fallbacks**: Use direct settings access

---

#### 5. Update Environment Configuration Files

**File**: `frontend/.env.local`

**Purpose**: Fix hostname mismatch in development

**Specific Changes**:
1. **Change backend URL from `127.0.0.1` to `localhost`**:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
   ```

---

**File**: `frontend/.env.example`

**Purpose**: Add guidance on hostname consistency

**Specific Changes**:
1. **Update comment for `NEXT_PUBLIC_API_URL`** to emphasize hostname consistency:
   ```
   # IMPORTANT: Use 'localhost' (not 127.0.0.1) to match the frontend hostname.
   # This ensures cookie-based authentication works correctly in development.
   # The frontend runs on localhost:3000, so the backend must also use localhost.
   ```

2. **Add note about cookie-based authentication**:
   ```
   # NOTE: Authentication uses HttpOnly cookies. The frontend and backend must
   # use the same hostname (both 'localhost' or both use the same domain) for
   # cookies to be shared correctly.
   ```

---

**File**: `.env.example`

**Purpose**: Add JWT cookie configuration variables

**Specific Changes**:
1. **Add new section after REST API & JWT section** (around line 180):
   ```
   # =============================================================================
   # JWT COOKIE CONFIGURATION
   # =============================================================================
   
   # Cookie domain for JWT tokens (access_token, refresh_token)
   # Development: Leave unset (defaults to None, cookies bound to exact hostname)
   # Production: Set to your domain with leading dot for subdomain sharing
   # Examples:
   #   .example.com  (shares cookies between api.example.com and app.example.com)
   #   localhost     (development only)
   # JWT_COOKIE_DOMAIN=
   
   # Cookie path (default: /)
   # JWT_COOKIE_PATH=/
   
   # Cookie SameSite attribute (default: Lax)
   # Options: Strict, Lax, None
   # JWT_COOKIE_SAMESITE=Lax
   
   # Cookie Secure flag (default: true in production, false in development)
   # Set to true to require HTTPS for cookie transmission
   # JWT_COOKIE_SECURE=true
   
   # Access token cookie max age in seconds (default: 300 = 5 minutes)
   # JWT_ACCESS_TOKEN_COOKIE_MAX_AGE=300
   
   # Refresh token cookie max age in seconds (default: 604800 = 7 days)
   # JWT_REFRESH_TOKEN_COOKIE_MAX_AGE=604800
   ```

2. **Update DEPLOYMENT NOTES section** to mention hostname consistency:
   ```
   # DEVELOPMENT:
   #   - Frontend and backend must use same hostname (both 'localhost')
   #   - Cookie-based authentication requires hostname consistency
   ```

---

#### 6. Update Documentation

**File**: `docs/ENVIRONMENT.md`

**Purpose**: Document JWT cookie configuration

**Specific Changes**:
1. **Add new section "JWT Cookie Configuration"** (after CORS section):
   - Explain cookie domain behavior (None vs ".example.com" vs "localhost")
   - Document all JWT cookie environment variables
   - Provide examples for development and production scenarios
   - Explain hostname consistency requirement
   - Document cookie security attributes (Secure, SameSite, HttpOnly)

2. **Update "Development Setup" section**:
   - Add note about using `localhost` (not `127.0.0.1`) for both frontend and backend
   - Explain why hostname consistency is required for cookie-based authentication

3. **Update "Production Deployment" section**:
   - Add JWT cookie configuration to deployment checklist
   - Provide example for subdomain cookie sharing

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bugs on unfixed code, then verify the fix works correctly and preserves existing behavior.

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the bugs BEFORE implementing the fix. Confirm or refute the root cause analysis. If we refute, we will need to re-hypothesize.

**Test Plan**: Write tests that simulate authentication flows with domain mismatches, inconsistent cookie parameters, and duplicated helper functions. Run these tests on the UNFIXED code to observe failures and understand the root causes.

**Test Cases**:
1. **Domain Mismatch Test**: Configure frontend on `localhost:3000` and backend on `127.0.0.1:8000`. Attempt login and verify that cookies are not accessible to frontend (will fail on unfixed code).

2. **Cookie Deletion Test**: Login to set cookies, then logout. Inspect browser cookies to verify they are not properly cleared due to parameter mismatch (will fail on unfixed code).

3. **Settings Fallback Test**: Search codebase for `getattr(django_settings, 'JWT_COOKIE_*')` patterns. Verify that settings are not defined in `settings/base.py`, confirming scattered defaults (will fail on unfixed code).

4. **Code Duplication Test**: Search for `_jwt_cookie_security` and `_set_jwt_cookie` functions. Verify they exist in multiple files with identical implementations (will fail on unfixed code).

5. **Header Auth Test**: Send request with Authorization header to authenticated endpoint. Verify that header-based authentication still works, confirming incomplete migration (will fail on unfixed code).

**Expected Counterexamples**:
- Cookies set by backend are not accessible to frontend due to domain mismatch
- Cookies are not properly cleared on logout due to parameter mismatch
- JWT cookie settings are not centrally defined, leading to scattered `getattr()` fallbacks
- Cookie helper functions are duplicated across multiple files
- Authorization header authentication is still supported alongside cookie authentication

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed system produces the expected behavior.

**Pseudocode:**
```
FOR ALL input WHERE isBugCondition(input) DO
  result := authenticateWithCookies_fixed(input)
  ASSERT expectedBehavior(result)
END FOR
```

**Test Cases**:
1. **Hostname Consistency Test**: Configure frontend and backend both on `localhost`. Login and verify cookies are accessible. Refresh token and verify new access token cookie is set. Logout and verify cookies are cleared.

2. **Centralized Utilities Test**: Verify that `src/api/utils/cookies.py` exists with `get_jwt_cookie_params()`, `set_jwt_cookie()`, and `delete_jwt_cookie()` functions. Verify all authentication views import and use these utilities.

3. **Settings Centralization Test**: Verify that `JWT_COOKIE_DOMAIN`, `JWT_COOKIE_PATH`, `JWT_COOKIE_SECURE`, `JWT_COOKIE_SAMESITE`, `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`, and `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE` are defined in `settings/base.py`.

4. **Cookie-Only Auth Test**: Send request with Authorization header to authenticated endpoint. Verify that header-based authentication is rejected and only cookie-based authentication works.

5. **Environment Config Test**: Verify that `frontend/.env.local` uses `localhost` (not `127.0.0.1`). Verify that `.env.example` includes JWT cookie configuration variables with documentation.

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed system produces the same result as the original system.

**Pseudocode:**
```
FOR ALL input WHERE NOT isBugCondition(input) DO
  ASSERT authenticateWithCookies_original(input) = authenticateWithCookies_fixed(input)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain
- It catches edge cases that manual unit tests might miss
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs

**Test Plan**: Observe behavior on UNFIXED code first for non-cookie operations (JWT token generation, user validation, tenant membership), then write property-based tests capturing that behavior.

**Test Cases**:
1. **JWT Token Generation Preservation**: Verify that JWT token generation logic (signing, claims, expiration) produces identical tokens before and after the fix.

2. **User Authentication Preservation**: Verify that user authentication logic (password validation, user lookup, permission checking) produces identical results before and after the fix.

3. **Tenant Membership Preservation**: Verify that tenant membership resolution and role checking produce identical results before and after the fix.

4. **API Endpoint Preservation**: Verify that non-authentication API endpoints (inventory, sales, reports) continue to work identically before and after the fix.

5. **Wagtail Admin Preservation**: Verify that Wagtail admin authentication (session-based) continues to work independently of JWT cookie changes.

### Unit Tests

- Test `get_jwt_cookie_params()` returns correct parameters from settings with proper defaults
- Test `set_jwt_cookie()` calls `response.set_cookie()` with all required parameters
- Test `delete_jwt_cookie()` calls `response.delete_cookie()` with matching parameters
- Test `CookieJWTAuthentication.authenticate()` reads from cookies only (not headers)
- Test login view sets both access_token and refresh_token cookies with correct max_age
- Test refresh view sets new access_token cookie with correct max_age
- Test logout view deletes both access_token and refresh_token cookies
- Test invitation accept view sets both cookies with correct max_age

### Property-Based Tests

- Generate random cookie parameters and verify `get_jwt_cookie_params()` returns consistent values
- Generate random JWT tokens and verify `set_jwt_cookie()` sets cookies with correct parameters
- Generate random authentication requests and verify cookie-based authentication works correctly
- Generate random user credentials and verify JWT token generation is unchanged by the fix
- Generate random tenant memberships and verify role checking is unchanged by the fix

### Integration Tests

- Test full login flow: POST to /auth/login/, verify cookies are set, verify subsequent requests are authenticated
- Test full refresh flow: POST to /auth/refresh/ with refresh_token cookie, verify new access_token cookie is set
- Test full logout flow: POST to /auth/logout/, verify cookies are deleted, verify subsequent requests are unauthenticated
- Test invitation accept flow: POST to /auth/invitations/<token>/accept/, verify cookies are set, verify user is authenticated
- Test cross-origin requests with CORS and credentials, verify cookies are sent and authentication works
- Test production subdomain scenario with JWT_COOKIE_DOMAIN=".example.com", verify cookies are shared across subdomains
