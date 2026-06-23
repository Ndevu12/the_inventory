"""Introspection endpoint exposing the set of loaded plugins."""

from __future__ import annotations

from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from plugins.manager import get_loaded_plugins


class InstalledPluginsView(APIView):
    """``GET /api/v1/plugins/`` — list installed plugins and their metadata."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="List installed plugins",
        description="Returns metadata for every loaded plugin (name, version, "
        "description, declared dependencies).",
        responses={200: dict},
    )
    def get(self, request):
        plugins = get_loaded_plugins()
        return Response({"count": len(plugins), "results": plugins})
