"""Public list of Wagtail content locales (for clients and tooling)."""

from __future__ import annotations

from django.utils.translation import get_language_info
from drf_spectacular.utils import OpenApiExample, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from wagtail.models import Locale

from home.i18n_sync import wagtail_locale_display_name


class WagtailLocalesListView(APIView):
    """Locales configured in Wagtail (Settings → Locales)."""

    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(
        summary="List Wagtail content locales",
        description=(
            "Returns active content locale codes and display metadata. "
            "Used by the Next.js app and `sync_frontend_locales`; "
            "add or remove locales in Wagtail admin."
        ),
        examples=[
            OpenApiExample(
                "Example",
                value=[
                    {
                        "code": "en",
                        "display_name": "English",
                        "is_rtl": False,
                        "is_default": True,
                    }
                ],
            )
        ],
        tags=["i18n"],
    )
    def get(self, request):
        payload = []
        for loc in Locale.objects.order_by("language_code"):
            try:
                info = get_language_info(loc.language_code)
                is_rtl = bool(info.get("bidi"))
            except Exception:
                is_rtl = False
            payload.append(
                {
                    "code": loc.language_code,
                    "display_name": wagtail_locale_display_name(loc),
                    "is_rtl": is_rtl,
                    "is_default": bool(loc.is_default),
                }
            )
        return Response(payload)
