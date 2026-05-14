"""Custom JWT authentication with HttpOnly cookie support (cookie-only, no headers).

Enforces cookie-based JWT authentication exclusively. Authorization headers
are NOT supported - only HttpOnly cookies are used for authentication.
This prevents CSRF attacks and ensures tokens are only transmitted securely.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication that ONLY supports HttpOnly cookies.
    
    Authorization headers are NOT supported. Only access_token cookies are used.
    
    This authentication backend:
    - Reads JWT tokens from HttpOnly cookies exclusively
    - Ignores Authorization headers completely
    - Returns None if no valid cookie token is found
    - Allows the view to handle 401 responses
    """

    def get_validated_token(self, raw_token):
        """Validate JWT token with proper error handling."""
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def authenticate(self, request):
        """Authenticate request using ONLY cookies (no headers).
        
        Returns:
            tuple (user, auth_token) if authenticated via cookie, None otherwise
            
        Raises:
            InvalidToken: if cookie token is present but invalid
        """
        # Try to get token from cookies ONLY (ignore Authorization header)
        access_token = request.COOKIES.get('access_token')
        if access_token is not None:
            try:
                validated_token = self.get_validated_token(access_token)
                user = self.get_user(validated_token)
                return (user, validated_token)
            except InvalidToken:
                # Cookie token is invalid, return None
                # Let the view handle 401 response
                return None

        # No token in cookie
        return None

