"""Resolve the Wagtail ``Locale`` for tenant-scoped seed data (canonical catalog rows)."""

from django.conf import settings
from django.utils import translation
from wagtail.models import Locale

from api.language import resolve_canonical_language_code, wagtail_locale_for_language


def _ensure_at_least_one_wagtail_locale():
    """Create a fallback locale when the table is empty (minimal test DBs, partial setups).

    Normal installs populate locales via Wagtail + ``home`` migrations; this keeps
    seeders and :class:`~wagtail.models.TranslatableMixin` saves from crashing when
    those rows are missing.
    """
    if Locale.objects.exists():
        return
    code = getattr(settings, "LANGUAGE_CODE", "en") or "en"
    try:
        code = translation.get_supported_language_variant(code)
    except LookupError:
        code = "en"
    short = (code or "en").replace("_", "-").split("-")[0].lower()
    Locale.objects.create(language_code=short)


def canonical_wagtail_locale_for_tenant(tenant):
    """Return the :class:`~wagtail.models.Locale` matching ``tenant.preferred_language``.

    Resolution order: Wagtail row for the canonical Django language code →
    :meth:`~wagtail.models.Locale.get_default` → any existing locale row (tests /
    minimal DBs may not match ``settings.LANGUAGE_CODE`` yet).
    """
    if tenant is None:
        return None
    _ensure_at_least_one_wagtail_locale()
    code = resolve_canonical_language_code(tenant)
    loc = wagtail_locale_for_language(code)
    if loc is not None:
        return loc
    try:
        return Locale.get_default()
    except Locale.DoesNotExist:
        pass
    return Locale.objects.order_by("pk").first()
