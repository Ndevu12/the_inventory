# Bugfix Requirements Document

## Introduction

The cookie-based JWT authentication system is not working properly between the frontend and backend due to domain mismatch issues and incomplete migration from header-based authentication. The frontend runs on `localhost:3000` while the backend API is configured as `127.0.0.1:8000`. Browsers treat `localhost` and `127.0.0.1` as different domains, preventing cookies set by the backend from being accessible to the frontend. Additionally, the backend lacks proper cookie domain configuration, making it incompatible with production subdomain scenarios. The system also still maintains support for header-based JWT authentication, creating inconsistency in the authentication approach.

This bug prevents users from logging in successfully via the browser-based frontend, as authentication cookies cannot be shared between the mismatched domains. The issue affects all cookie-based authentication flows including login, token refresh, and logout. The goal is to complete the full migration to cookie-based authentication exclusively, removing header-based authentication support to ensure consistency.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the frontend runs on `localhost:3000` and the backend API is configured as `127.0.0.1:8000` THEN cookies set by the backend cannot be read by the frontend due to browser domain mismatch

1.2 WHEN the backend sets authentication cookies via `set_cookie()` without specifying a `domain` parameter THEN cookies are bound to the exact request domain and cannot be shared across subdomains or hostname variations

1.3 WHEN the backend calls `delete_cookie()` during logout without matching the original `domain`, `path`, `secure`, and `samesite` parameters THEN cookies may not be properly cleared from the browser

1.4 WHEN JWT cookie settings like `JWT_COOKIE_DOMAIN`, `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`, and `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE` are referenced in code but not defined in `settings/base.py` THEN the system relies on scattered hardcoded defaults using `getattr()` fallbacks, leading to inconsistent configuration

1.5 WHEN the frontend `.env.local` file uses `127.0.0.1` instead of `localhost` THEN the domain mismatch prevents cookie-based authentication from working in development

1.6 WHEN the authentication system still supports header-based JWT authentication (Authorization: Bearer) THEN it creates inconsistency and confusion about the primary authentication method, contradicting the full migration to cookie-based authentication

1.7 WHEN cookie setting and deletion logic is duplicated across multiple files (`src/api/views/auth.py` lines 49-68, 104-112, 134-143 and `src/api/views/invitations.py` lines 55-67, 234-247) with helper functions `_jwt_cookie_security()` and `_set_jwt_cookie()` THEN it leads to inconsistent implementations, maintenance burden, and potential bugs when cookie parameters need to be updated

1.8 WHEN authentication utilities and helpers are scattered across different modules without a centralized location THEN it violates the DRY (Don't Repeat Yourself) principle and makes the codebase harder to maintain and test

1.9 WHEN the `src/api` module lacks a `utils/` directory structure THEN there is no established pattern for shared utilities, unlike other Django apps that typically organize reusable functions in a utils module

### Expected Behavior (Correct)

2.1 WHEN the frontend runs on `localhost:3000` and the backend API is configured as `localhost:8000` THEN cookies set by the backend SHALL be accessible to the frontend, enabling successful authentication

2.2 WHEN the backend sets authentication cookies via `set_cookie()` THEN it SHALL specify an appropriate `domain` parameter that works for both development (localhost) and production (subdomain) scenarios

2.3 WHEN the backend calls `delete_cookie()` during logout THEN it SHALL use matching `domain`, `path`, `secure`, and `samesite` parameters to ensure cookies are properly cleared

2.4 WHEN JWT cookie settings are needed THEN they SHALL be defined centrally in `settings/base.py` with appropriate defaults for `JWT_COOKIE_DOMAIN`, `JWT_COOKIE_SECURE`, `JWT_COOKIE_SAMESITE`, `JWT_COOKIE_PATH`, `JWT_ACCESS_TOKEN_COOKIE_MAX_AGE`, and `JWT_REFRESH_TOKEN_COOKIE_MAX_AGE`

2.5 WHEN the frontend `.env.local` and `.env.example` files specify the backend API URL THEN they SHALL use `localhost` consistently to match the frontend domain and enable cookie sharing

2.6 WHEN environment configuration examples are provided THEN they SHALL include guidance on hostname consistency and JWT cookie configuration variables

2.7 WHEN the authentication system processes requests THEN it SHALL use cookie-based JWT authentication exclusively as the primary and only authentication method for browser clients

2.8 WHEN the backend authentication middleware and views authenticate requests THEN they SHALL read JWT tokens from cookies only, removing support for Authorization header-based authentication

2.9 WHEN API documentation and tests reference authentication THEN they SHALL demonstrate and validate cookie-based authentication as the standard method

2.10 WHEN cookie operations (setting, deleting, reading) are needed THEN they SHALL be handled by a centralized cookie utility module (`src/api/utils/cookies.py`) that provides reusable functions (`get_jwt_cookie_params()`, `set_jwt_cookie()`, `delete_jwt_cookie()`) for consistent cookie management

2.11 WHEN authentication views (`src/api/views/auth.py`, `src/api/views/invitations.py`) need to set or delete JWT cookies THEN they SHALL import and use the centralized cookie utility functions, removing all duplicated helper functions like `_jwt_cookie_security()` and `_set_jwt_cookie()`

2.12 WHEN the `src/api/utils/` directory is created THEN it SHALL follow Django best practices with an `__init__.py` file and organized utility modules (starting with `cookies.py`)

2.13 WHEN cookie parameters (domain, path, secure, samesite, httponly, max_age) need to be retrieved THEN they SHALL be obtained from a single `get_jwt_cookie_params()` function that reads from Django settings with appropriate defaults

2.14 WHEN multiple views or modules need to perform cookie operations THEN they SHALL import from `api.utils.cookies` and use the same centralized utility functions to ensure consistency across the entire authentication system

2.15 WHEN the centralized cookie utilities are implemented THEN they SHALL be designed to be easily testable in isolation, with clear function signatures and comprehensive docstrings

### Unchanged Behavior (Regression Prevention)

3.1 WHEN existing tests for authentication endpoints run THEN they SHALL CONTINUE TO pass with modifications to use cookie-based authentication instead of header-based

3.2 WHEN the system runs in production with proper subdomain configuration THEN cookie-based authentication SHALL CONTINUE TO work as designed

3.3 WHEN Django session cookies are used for Wagtail admin authentication THEN they SHALL CONTINUE TO function independently of JWT cookie changes

3.4 WHEN CORS settings allow credentials THEN the system SHALL CONTINUE TO support cross-origin authenticated requests with cookies

3.5 WHEN the backend authentication middleware processes requests THEN it SHALL prioritize cookie-based JWT authentication as the primary method

3.6 WHEN API documentation is generated THEN it SHALL reflect cookie-based authentication as the standard authentication method

3.7 WHEN the centralized cookie utilities are implemented THEN all duplicated cookie helper functions (`_jwt_cookie_security()`, `_set_jwt_cookie()`) in `src/api/views/auth.py` and `src/api/views/invitations.py` SHALL be removed and replaced with imports from the centralized module
