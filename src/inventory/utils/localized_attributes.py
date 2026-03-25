"""Wagtail-localized attribute reads for ORM instances (domain layer, API-agnostic)."""

from __future__ import annotations

from typing import Any


def attribute_in_display_locale(
    source: Any,
    attr: str,
    display_locale,
) -> Any:
    """Return *attr* from the translation in *display_locale*, else from *source*."""
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
