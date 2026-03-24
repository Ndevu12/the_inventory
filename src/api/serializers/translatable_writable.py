"""DRF create/update for Wagtail ``TranslatableMixin`` catalog rows (I18N-16).

**Write locale** uses :func:`api.language.resolve_write_language_code`: ``?language=``
when present, otherwise the tenant **canonical** locale. ``Accept-Language`` is not
used for writes.

- **POST** in the canonical locale: start a new translation group (omit ``translation_of``).
- **POST** in another locale: set ``translation_of`` to the PK of the **canonical**
  row (the id returned by default list/detail).
- **PATCH** with ``?language=`` updates that locale’s row (creating the linked
  translation first when needed). The URL ``id`` stays the canonical list id.
"""

from __future__ import annotations

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from wagtail.models import TranslatableMixin

from inventory.services.localization import copy_catalog_row_for_locale
from tenants.middleware import get_effective_tenant


class TranslatableWritableMixin:
    """Set ``locale`` on create, resolve / bootstrap translation rows on update."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = self.Meta.model
        self.fields["translation_of"] = serializers.PrimaryKeyRelatedField(
            queryset=model.objects.all(),
            write_only=True,
            required=False,
            allow_null=True,
            help_text=(
                "Required when POSTing in a non-canonical locale: PK of the canonical "
                "locale row (default list/detail id)."
            ),
        )

    def _write_locale(self):
        loc = self.context.get("wagtail_write_locale")
        if loc is None:
            raise ValidationError(
                {
                    "detail": "No Wagtail Locale matches the resolved language; "
                    "configure Locales in Wagtail admin."
                }
            )
        return loc

    def _canonical_locale(self):
        loc = self.context.get("wagtail_canonical_locale")
        if loc is None:
            raise ValidationError({"detail": "Could not resolve the tenant canonical locale."})
        return loc

    def _same_translation_group_qs(self, qs, instance):
        if instance is not None and getattr(instance, "translation_key", None):
            return qs.exclude(translation_key=instance.translation_key)
        if instance is not None:
            return qs.exclude(pk=instance.pk)
        return qs

    def validate(self, attrs):
        attrs = super().validate(attrs)
        translation_of = attrs.get("translation_of")
        write_loc = self.context.get("wagtail_write_locale")
        canon_loc = self.context.get("wagtail_canonical_locale")
        if self.instance is None and translation_of is not None and write_loc and canon_loc:
            if write_loc.id == canon_loc.id:
                raise ValidationError(
                    {"translation_of": ["Omit this field when creating in the canonical locale."]}
                )
        return attrs

    def _localize_relation(self, related, target_locale):
        if related is None or target_locale is None:
            return related
        if not isinstance(related, TranslatableMixin):
            return related
        if related.locale_id == target_locale.id:
            return related
        translated = related.get_translation_or_none(target_locale)
        return translated if translated is not None else related

    def _apply_localized_fks(self, validated_data, loc):
        if "category" in validated_data:
            validated_data["category"] = self._localize_relation(
                validated_data.get("category"), loc,
            )
        return validated_data

    def _assign_translated_fields(self, translated, validated_data, write_loc):
        for field, value in validated_data.items():
            if field == "category":
                setattr(
                    translated,
                    "category",
                    self._localize_relation(value, write_loc),
                )
            else:
                setattr(translated, field, value)

    def create(self, validated_data):
        translation_of = validated_data.pop("translation_of", None)
        write_loc = self._write_locale()
        canon_loc = self._canonical_locale()
        model = self.Meta.model
        request = self.context.get("request")
        tenant = validated_data.get("tenant") or (
            get_effective_tenant(request) if request else None
        )

        if not issubclass(model, TranslatableMixin):
            return super().create(validated_data)

        if write_loc.id == canon_loc.id:
            if translation_of is not None:
                raise ValidationError(
                    {"translation_of": ["Omit this field when creating in the canonical locale."]}
                )
            validated_data["locale"] = write_loc
            validated_data = self._apply_localized_fks(validated_data, write_loc)
            return self._create_canonical_row(validated_data)

        if translation_of is None:
            raise ValidationError(
                {
                    "translation_of": [
                        "This field is required when creating in a non-canonical locale."
                    ],
                }
            )

        source = translation_of
        if tenant and source.tenant_id != tenant.pk:
            raise ValidationError({"translation_of": ["Object does not belong to this tenant."]})
        if source.locale_id != canon_loc.id:
            raise ValidationError(
                {
                    "translation_of": [
                        "Must reference the row in the tenant's canonical locale "
                        "(default list/detail id)."
                    ],
                }
            )
        if source.get_translation_or_none(write_loc) is not None:
            raise ValidationError(
                {
                    "translation_of": [
                        "A translation for this locale already exists; use PATCH with ?language=."
                    ],
                }
            )

        translated = copy_catalog_row_for_locale(source, write_loc)
        self._assign_translated_fields(translated, validated_data, write_loc)
        translated.save()
        return translated

    def _create_canonical_row(self, validated_data):
        """Create a new row in the canonical locale (override for MP_Tree ``Category``)."""
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data.pop("translation_of", None)
        loc = self._write_locale()
        validated_data.pop("locale", None)
        validated_data = self._apply_localized_fks(validated_data, loc)

        model = self.Meta.model
        if not issubclass(model, TranslatableMixin) or not isinstance(instance, TranslatableMixin):
            return super().update(instance, validated_data)

        if instance.locale_id == loc.id:
            return super().update(instance, validated_data)

        target = instance.get_translation_or_none(loc)
        if target is None:
            canon_loc = self._canonical_locale()
            source = (
                instance
                if instance.locale_id == canon_loc.id
                else instance.get_translation_or_none(canon_loc)
            )
            if source is None:
                source = instance
            target = copy_catalog_row_for_locale(source, loc)

        return super().update(target, validated_data)
