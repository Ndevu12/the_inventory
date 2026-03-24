"""Sync Django/Wagtail language settings from ``wagtailcore.Locale`` rows.

Wagtail admin (Settings → Locales) and seeders own which locales exist. This
module merges those rows into :setting:`LANGUAGES` and
:setting:`WAGTAIL_CONTENT_LANGUAGES` and clears translation caches so runtime
changes take effect without a process restart.
"""

from __future__ import annotations

from django.apps import apps
from django.conf import global_settings
from django.conf import settings
from django.db import OperationalError, ProgrammingError


def wagtail_locale_display_name(loc) -> str:
    """Human label for a Wagtail ``Locale`` (admin name, else Django catalog, else code)."""
    from django.utils.translation import get_language_info

    label = str(loc).strip()
    code = loc.language_code
    if label and label != code:
        return label
    try:
        return str(get_language_info(code)["name"])
    except KeyError:
        pass
    merged = dict(global_settings.LANGUAGES)
    if "rw" not in merged:
        merged["rw"] = "Kinyarwanda"
    try:
        merged.update(dict(settings.LANGUAGES))
    except Exception:
        pass
    return merged.get(code, code)


def refresh_i18n_settings_from_wagtail() -> None:
    """Update language settings from the database and clear i18n caches."""
    if not apps.ready:
        return

    try:
        from wagtail.models import Locale
    except LookupError:
        return

    try:
        locales = list(Locale.objects.order_by("language_code"))
    except (OperationalError, ProgrammingError):
        return

    if not locales:
        return

    lang_dict = dict(global_settings.LANGUAGES)
    if "rw" not in lang_dict:
        lang_dict["rw"] = "Kinyarwanda"

    wagtail_pairs: list[tuple[str, str]] = []
    for loc in locales:
        code = loc.language_code
        label = wagtail_locale_display_name(loc)
        wagtail_pairs.append((code, label))
        if code not in lang_dict:
            lang_dict[code] = label

    settings.LANGUAGES = tuple(sorted(lang_dict.items(), key=lambda x: x[0]))
    settings.WAGTAIL_CONTENT_LANGUAGES = wagtail_pairs

    _clear_i18n_caches()


def _clear_i18n_caches() -> None:
    from django.utils.translation import trans_real
    from wagtail import coreutils

    trans_real.get_languages.cache_clear()
    trans_real.get_supported_language_variant.cache_clear()
    coreutils.get_content_languages.cache_clear()
    coreutils.get_supported_content_language_variant.cache_clear()
