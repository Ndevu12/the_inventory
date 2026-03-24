"""Helpers for overlaying Wagtail translation fields in API serializers."""

from __future__ import annotations

from typing import Any

from api.language import wagtail_locale_for_language


def display_locale_from_context(context: dict | None) -> Any:
    """Resolve Wagtail ``Locale`` for serializer output.

    Prefers ``wagtail_display_locale``; falls back to ``language`` (Django code)
    via :func:`~api.language.wagtail_locale_for_language` so tests and custom
    call sites can pass either.
    """
    if not context:
        return None
    loc = context.get("wagtail_display_locale")
    if loc is not None:
        return loc
    code = context.get("language")
    if code:
        return wagtail_locale_for_language(code)
    return None


def attribute_in_display_locale(
    source: Any,
    attr: str,
    display_locale,
) -> Any:
    """Return ``attr`` from the translation in *display_locale*, else from *source*."""
    if source is None:
        return None
    if display_locale is None:
        return getattr(source, attr, None)
    getter = getattr(source, "get_translation_or_none", None)
    if not callable(getter):
        return getattr(source, attr)
    trans = getter(display_locale)
    if trans is not None:
        return getattr(trans, attr)
    return getattr(source, attr)
