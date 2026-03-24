"""Programmatic wagtail-localize flows for tenant catalog models (API authoring)."""

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
