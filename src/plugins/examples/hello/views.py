"""A trivial endpoint demonstrating a plugin-contributed API view."""

from __future__ import annotations

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from plugins.settings import plugin_setting
from tenants.context import get_current_tenant


class HelloView(APIView):
    """``GET /api/v1/hello/`` — proves a plugin can serve tenant-scoped data."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = get_current_tenant()
        greeting = plugin_setting("hello", "GREETING", default="Hello")
        return Response(
            {
                "message": f"{greeting} from the hello plugin!",
                "tenant": getattr(tenant, "name", None),
            }
        )
