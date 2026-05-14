"""Centralized JWT cookie management utilities.

This module provides reusable functions for consistent HTTP cookie handling
across the authentication system. By centralizing cookie logic here, we ensure:

1. Cookie parameters (domain, path, secure, samesite, httponly, max_age) are
   consistent across all views and middleware
2. Settings are read from Django settings (with env var overrides) in one place
3. Code duplication is eliminated (previously duplicated in auth.py and invitations.py)
4. Cookie operations are easily testable in isolation

Usage:
    from api.utils.cookies import get_jwt_cookie_params, set_jwt_cookie, delete_jwt_cookie

    # Get all cookie parameters from Django settings
    params = get_jwt_cookie_params()

    # Set a JWT cookie with all appropriate parameters
    set_jwt_cookie(response, 'access_token', token_value, max_age=300)

    # Delete a JWT cookie with matching parameters
    delete_jwt_cookie(response, 'access_token')
"""

from django.conf import settings


def get_jwt_cookie_params() -> dict:
    """Get JWT cookie parameters from Django settings.

    Retrieves all JWT cookie configuration from Django settings with proper
    defaults. This is the single source of truth for cookie parameters used
    throughout the authentication system.

    Returns:
        dict: Cookie parameters with keys:
            - domain: str | None - Cookie domain (see JWT_COOKIE_DOMAIN setting)
            - path: str - Cookie path (default: "/")
            - secure: bool - HTTPS only flag (default: False in dev, True in prod)
            - samesite: str - Cross-site flag ("Lax", "Strict", "None")
            - httponly: bool - HTTP only flag (always True for security)

    Examples:
        >>> params = get_jwt_cookie_params()
        >>> params['secure']
        False  # In development (DEBUG=True)

        # With production settings (JWT_COOKIE_SECURE=true via env)
        >>> params['secure']
        True

        # With custom domain (JWT_COOKIE_DOMAIN=".example.com" via env)
        >>> params['domain']
        ".example.com"
    """
    return {
        "domain": getattr(settings, "JWT_COOKIE_DOMAIN", None),
        "path": getattr(settings, "JWT_COOKIE_PATH", "/"),
        "secure": getattr(settings, "JWT_COOKIE_SECURE", False),
        "samesite": getattr(settings, "JWT_COOKIE_SAMESITE", "Lax"),
        "httponly": True,  # Always True for security
    }


def set_jwt_cookie(response, key: str, value: str, max_age: int) -> None:
    """Set a JWT cookie with consistent parameters.

    Sets an HTTP cookie with JWT token value using parameters from Django settings.
    Ensures all JWT cookies use consistent domain, path, secure, samesite, and httponly
    flags throughout the application.

    Args:
        response: Django HttpResponse object to set cookie on
        key: Cookie name (e.g., 'access_token' or 'refresh_token')
        value: Cookie value (JWT token string)
        max_age: Cookie lifetime in seconds. Should match token lifetime:
            - get_jwt_cookie_params()['access_token_max_age'] = 300 (5 min)
            - get_jwt_cookie_params()['refresh_token_max_age'] = 604800 (7 days)

    Returns:
        None. Modifies response object in place.

    Examples:
        >>> from rest_framework.response import Response
        >>> response = Response({"status": "logged in"})
        >>> set_jwt_cookie(response, 'access_token', 'eyJ...token...', max_age=300)
        >>> response.cookies['access_token']['max-age']
        300
        >>> response.cookies['access_token']['httponly']
        True
    """
    params = get_jwt_cookie_params()
    response.set_cookie(
        key,
        value,
        domain=params["domain"],
        path=params["path"],
        secure=params["secure"],
        samesite=params["samesite"],
        httponly=params["httponly"],
        max_age=max_age,
    )


def delete_jwt_cookie(response, key: str) -> None:
    """Delete a JWT cookie with matching parameters.

    Deletes an HTTP cookie by using the same parameters that were used when
    setting it. This is critical for proper cookie deletion - browsers only
    delete cookies when domain, path, secure, and samesite all match the
    original set_cookie call.

    Args:
        response: Django HttpResponse object to delete cookie from
        key: Cookie name to delete (e.g., 'access_token' or 'refresh_token')

    Returns:
        None. Modifies response object in place.

    Examples:
        >>> from rest_framework.response import Response
        >>> response = Response({"status": "logged out"})
        >>> delete_jwt_cookie(response, 'access_token')
        >>> delete_jwt_cookie(response, 'refresh_token')
        >>> response.cookies['access_token'].value
        ''
    """
    params = get_jwt_cookie_params()
    response.delete_cookie(
        key,
        domain=params["domain"],
        path=params["path"],
        samesite=params["samesite"],
    )
