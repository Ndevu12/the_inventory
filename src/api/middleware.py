"""JWT authentication middleware.

DRF also authenticates at the view layer; this runs earlier so
``request.user`` is set before :class:`tenants.middleware.TenantMiddleware`
resolves ``request.tenant`` from memberships (Bearer token flows).
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
