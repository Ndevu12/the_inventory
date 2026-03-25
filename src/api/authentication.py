"""Custom JWT authentication with cookie support.

Supports both header-based JWT (Authorization: Bearer) and HttpOnly cookie-based JWT.
Header takes precedence over cookie (explicit header auth > implicit cookie auth).
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication that supports HttpOnly cookies as fallback to headers.
    
    Authentication order:
    1. Authorization: Bearer <token> header (explicit auth)
    2. access_token cookie (implicit browser auth)
    
    This allows:
    - Mobile/API clients to use header-based JWT
    - Browser clients to use cookie-based JWT automatically
    - Header to override cookie if both present
    """

    def get_validated_token(self, raw_token):
        """Validate JWT token with proper error handling."""
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def authenticate(self, request):
        """Authenticate request using header or cookie.
        
        Returns:
            tuple (user, auth_token) if authenticated, None if no token found
            
        Raises:
            InvalidToken: if token is present but invalid
        """
        # First, try to get token from Authorization header (explicit auth)
        auth = super().authenticate(request)
        if auth is not None:
            return auth

        # If no header token, try to get from cookies (implicit browser auth)
        access_token = request.COOKIES.get('access_token')
        if access_token is not None:
            try:
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except InvalidToken:
                # Cookie token is invalid, but don't fail here
                # Let the view handle the 401 response
                return None

        # No token in header or cookie
        return None
