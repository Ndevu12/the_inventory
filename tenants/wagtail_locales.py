"""Wagtail-driven language choices (Settings → Locales).

`Tenant.preferred_language` and similar fields should use these callables so the
set of supported languages is edited in the admin, not in Django settings.
"""

from wagtail.models import Locale


def wagtail_locale_choices():
    """Return (language_code, label) pairs for model/form ``choices``.

    Falls back to English when no locales exist yet (e.g. before first Wagtail
    setup), so defaults and migrations remain usable.
    """

    locales = list(Locale.objects.order_by("language_code"))
    if not locales:
        return [("en", "English")]
    return [(loc.language_code, str(loc)) for loc in locales]
