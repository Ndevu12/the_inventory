"""Custom JWT authentication with HttpOnly cookie and Authorization header support.

Supports both cookie-based and header-based JWT authentication for flexibility.
Prioritizes cookies for browser-based clients, but also supports Authorization
headers for API clients (tests, mobile apps, etc.).

This module provides centralized token extraction and validation logic that can
be reused across different authentication flows and features.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


class CookieJWTAuthentication(JWTAuthentication):
    """JWT authentication supporting both HttpOnly cookies and Authorization headers.
    
    This authentication backend:
    - Reads JWT tokens from HttpOnly cookies first (preferred for browsers)
    - Falls back to Authorization headers if no cookie is found
    - Supports flexible authentication for different client types
    - Returns None if no valid token is found
    - Allows the view to handle 401 responses
    - Provides reusable token extraction methods for other features
    """

    def get_validated_token(self, raw_token):
        """Validate JWT token with proper error handling."""
        try:
            return super().get_validated_token(raw_token)
        except InvalidToken as e:
            raise InvalidToken(f"Invalid token: {str(e)}")

    def extract_token_from_cookie(self, request):
        """Extract JWT token from HttpOnly cookie.
        
        Looks for the 'access_token' cookie in the request.
        
        Args:
            request: Django request object
            
        Returns:
            str: Token string if found, None otherwise
        """
        return request.COOKIES.get('access_token')

    def extract_token_from_header(self, request):
        """Extract JWT token from Authorization header.
        
        Expects Authorization header in format: 'Bearer <token>'
        
        Args:
            request: Django request object
            
        Returns:
            str: Token string if found and properly formatted, None otherwise
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]  # Remove 'Bearer ' prefix
            return token if token else None
        return None

    def extract_token(self, request, from_cookie=True, from_header=True):
        """Extract JWT token from request using configured sources.
        
        Provides flexible token extraction with configurable priority.
        By default, prioritizes cookies over headers.
        
        Args:
            request: Django request object
            from_cookie: bool - Whether to extract from cookies (default: True)
            from_header: bool - Whether to extract from Authorization header (default: True)
            
        Returns:
            str: Token string if found from any configured source, None otherwise
            
        Example:
            # Extract from cookies first, then headers
            token = auth.extract_token(request, from_cookie=True, from_header=True)
            
            # Extract only from headers
            token = auth.extract_token(request, from_cookie=False, from_header=True)
        """
        # Try cookie first if enabled (preferred for browser clients)
        if from_cookie:
            token = self.extract_token_from_cookie(request)
            if token is not None:
                return token

        # Fall back to header if enabled (for API clients)
        if from_header:
            token = self.extract_token_from_header(request)
            if token is not None:
                return token

        return None

    def validate_and_authenticate_token(self, token):
        """Validate token and retrieve associated user.
        
        Centralizes token validation and user retrieval logic for reuse
        across different authentication flows.
        
        Args:
            token (str): Raw JWT token string
            
        Returns:
            tuple: (user, validated_token) if successful, None if invalid
            
        Example:
            result = auth.validate_and_authenticate_token(token_string)
            if result:
                user, validated_token = result
            else:
                # Handle invalid token
        """
        try:
            validated_token = self.get_validated_token(token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except InvalidToken:
            return None

    def authenticate(self, request):
        """Authenticate request using cookies or Authorization headers.
        
        Priority:
        1. HttpOnly cookie (access_token) - preferred for browser clients
        2. Authorization header (Bearer token) - for API clients
        
        Returns:
            tuple (user, auth_token) if authenticated, None otherwise
            
        Raises:
            InvalidToken: if token is present but invalid
        """
        # Extract token from request (prioritizes cookies)
        access_token = self.extract_token(request, from_cookie=True, from_header=True)
        
        if not access_token:
            # No token found
            return None

        # Validate token and retrieve user
        return self.validate_and_authenticate_token(access_token)

