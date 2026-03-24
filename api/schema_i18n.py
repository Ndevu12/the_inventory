"""OpenAPI fragments for catalog i18n (I18N-10)."""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter

OPENAPI_LANGUAGE_QUERY_PARAMETER = OpenApiParameter(
    name="language",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Translatable catalog locale. **GET:** overlay strings; resolution order is "
        "this parameter, tenant preferred_language, then Accept-Language. "
        "**POST/PATCH/PUT:** target locale for the persisted row; when omitted, the "
        "tenant canonical locale is used (Accept-Language is ignored). "
        "Invalid codes return 400. For POST in a non-canonical locale, send "
        "`translation_of` (canonical row id) in the body—see serializer schema."
    ),
)
