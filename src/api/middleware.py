"""JWT authentication middleware.

DRF also authenticates at the view layer; this runs earlier so
``request.user`` is set before :class:`tenants.middleware.TenantMiddleware`
resolves ``request.tenant`` from memberships (Bearer token flows).

Supports both header-based JWT (Authorization: Bearer) and cookie-based JWT
for browser clients.
"""

import logging

from api.authentication import CookieJWTAuthentication

logger = logging.getLogger(__name__)


class JWTAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_auth = CookieJWTAuthentication()

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
            # Authentication is best-effort here: DRF re-runs it at the view
            # layer and returns a proper 401. Leave request.user anonymous and
            # log for diagnostics rather than failing the whole request.
            logger.debug("JWT middleware authentication failed", exc_info=True)
