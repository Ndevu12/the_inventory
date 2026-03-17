"""JWT authentication middleware.

DRF's authentication runs at the view layer, after all middleware.
This middleware pre-authenticates JWT requests so that ``request.user``
is available to ``TenantMiddleware`` for automatic tenant resolution
from user memberships.
"""

from rest_framework_simplejwt.authentication import JWTAuthentication


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = JWTAuthentication()

    def __call__(self, request):
        if not hasattr(request, "user") or request.user.is_anonymous:
            self._try_jwt_auth(request)
        return self.get_response(request)

    def _try_jwt_auth(self, request):
        try:
            result = self.jwt_auth.authenticate(request)
            if result is not None:
                request.user, request.auth = result
        except Exception:
            pass
