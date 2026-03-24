"""Resolve language for tenant API reads (query param, tenant default, Accept-Language)."""

from django.conf import settings
from django.utils import translation
from rest_framework.exceptions import ValidationError
from wagtail.models import Locale


def _language_query_value(request, key: str = "language"):
    """DRF ``Request.query_params`` or Django ``GET``."""
    params = getattr(request, "query_params", None)
    if params is not None:
        return params.get(key)
    return request.GET.get(key)


def resolve_display_language_code(request, tenant) -> str:
    """Return Django language code for this request (gettext + Wagtail lookups).

    Order: ``?language=`` → ``tenant.preferred_language`` → ``Accept-Language`` →
    ``settings.LANGUAGE_CODE``.

    Raises ``ValidationError`` when ``language`` is present but not supported by Django.
    """
    raw = _language_query_value(request, "language")
    if raw is not None and str(raw).strip() == "":
        raw = None
    if raw is not None:
        try:
            return translation.get_supported_language_variant(raw)
        except LookupError as exc:
            raise ValidationError(
                {"language": ["Unsupported or invalid language code."]}
            ) from exc

    pref = getattr(tenant, "preferred_language", None) or ""
    pref = str(pref).strip()
    if pref:
        try:
            return translation.get_supported_language_variant(pref)
        except LookupError:
            pass

    from_request = translation.get_language_from_request(request, check_path=False)
    if from_request:
        try:
            return translation.get_supported_language_variant(from_request)
        except LookupError:
            pass

    return translation.get_supported_language_variant(settings.LANGUAGE_CODE)


def resolve_canonical_language_code(tenant) -> str:
    """Language code for the tenant's primary locale rows (stable ids, FKs, stock)."""
    pref = getattr(tenant, "preferred_language", None) or ""
    pref = str(pref).strip() or settings.LANGUAGE_CODE
    try:
        return translation.get_supported_language_variant(pref)
    except LookupError:
        return translation.get_supported_language_variant(settings.LANGUAGE_CODE)


def resolve_write_language_code(request, tenant) -> str:
    """Language code for **writes** to translatable catalog rows (I18N-16).

    Unlike :func:`resolve_display_language_code`, this does **not** fall back to
    ``Accept-Language``: absent or blank ``language`` means the tenant **canonical**
    locale only. When ``language`` is present, it must be a supported Django code.
    """
    raw = _language_query_value(request, "language")
    if raw is not None and str(raw).strip() == "":
        raw = None
    if raw is not None:
        try:
            return translation.get_supported_language_variant(raw)
        except LookupError as exc:
            raise ValidationError(
                {"language": ["Unsupported or invalid language code."]}
            ) from exc
    return resolve_canonical_language_code(tenant)


def wagtail_locale_for_language(code: str) -> Locale | None:
    """Return Wagtail ``Locale`` for *code*, or ``None`` if not configured.

    Prefer :meth:`~wagtail.models.Locale.objects.get_for_language` when the code
    is in ``WAGTAIL_CONTENT_LANGUAGES``. Fall back to an exact ``language_code``
    row so API ``?language=`` works for locales created in Wagtail admin even if
    settings lag behind.
    """
    if not code:
        return None
    try:
        return Locale.objects.get_for_language(code)
    except (Locale.DoesNotExist, LookupError):
        pass
    normalized = code.replace("_", "-").strip().lower()
    loc = Locale.objects.filter(language_code__iexact=normalized).first()
    if loc is not None:
        return loc
    short = normalized.split("-")[0]
    if short != normalized:
        loc = Locale.objects.filter(language_code__iexact=short).first()
    return loc
