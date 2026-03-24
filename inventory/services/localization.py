"""Programmatic wagtail-localize flows for tenant catalog models (API authoring).

Domain copy (product name, etc.) lives in the DB as linked rows per Wagtail locale.
Create or update those via this service and translatable serializers; use ``GET`` with
``?language=`` (sent automatically from the Next.js UI locale) to read overlays. Static UI
strings belong in ``frontend/public/locales/*.json``, not here. See
``tests/api/test_api_i18n_authoring.py`` for API examples.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework.exceptions import ValidationError

if TYPE_CHECKING:
    from wagtail.models import Locale

from inventory.models import Category


def category_translation_from_source(source: Category, target_locale: Locale) -> Category:
    """Create an unsaved French (etc.) category row linked to *source*, fixing MP_Tree paths.

    Wagtail's default :meth:`~wagtail.models.TranslatableMixin.copy_for_translation` copies
    ``path``/``depth``/``numchild``, which breaks treebeard's unique ``path`` constraint.
    """
    clone = source.copy_for_translation(
        target_locale,
        exclude_fields=["path", "depth", "numchild"],
    )
    if source.depth == 1:
        Category.add_root(instance=clone)
    else:
        parent = source.get_parent()
        parent_t = parent.get_translation_or_none(target_locale)
        if parent_t is None:
            raise ValidationError(
                {
                    "translation_of": [
                        "Translate the parent category into this locale first, then add the child translation."
                    ]
                }
            )
        parent_t.add_child(instance=clone)
    return clone


def copy_catalog_row_for_locale(source, target_locale: Locale):
    """Return a saved instance of *source* in *target_locale*, linked by ``translation_key``.

    Idempotent: returns the existing translation row if present.
    """
    if source.locale_id == target_locale.id:
        return source
    existing = source.get_translation_or_none(target_locale)
    if existing is not None:
        return existing
    if isinstance(source, Category):
        return category_translation_from_source(source, target_locale)
    clone = source.copy_for_translation(target_locale)
    clone.save()
    return clone
