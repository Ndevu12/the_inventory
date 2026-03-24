"""Bootstrap :class:`~wagtail.models.Locale` rows for fresh environments.

Change ``DEFAULT_LOCALE_CODES`` when you want different defaults for
``seed_database``. Staff can add or remove locales later in Wagtail admin
(Settings → Locales); those edits are the ongoing source of truth.
"""

from __future__ import annotations

DEFAULT_LOCALE_CODES: tuple[str, ...] = (
    "en",
    "fr",
    "sw",
    "rw",
    "es",
    "ar",
)


def ensure_default_wagtail_locales(*, verbose: bool = False) -> bool:
    """Ensure seed locale codes exist as Wagtail ``Locale`` rows.

    Returns:
        True if at least one locale row was created.
    """
    from wagtail.models import Locale

    created_any = False
    for code in DEFAULT_LOCALE_CODES:
        _obj, created = Locale.objects.get_or_create(language_code=code)
        if created:
            created_any = True
            if verbose:
                print(f"  ✓ Created Wagtail Locale: {code}")
    return created_any
