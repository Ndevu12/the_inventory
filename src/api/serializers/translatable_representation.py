"""Merge Wagtail translation field values into serializer output for ``?language=``."""

from api.serializers.localized_strings import display_locale_from_context


class TranslatableRepresentationMixin:
    """Overlay string fields from ``get_translation_or_none(display_locale)``.

    Reads display locale from serializer context: ``wagtail_display_locale`` or
    ``language`` (see :func:`~api.serializers.localized_strings.display_locale_from_context`),
    typically set by :class:`~api.mixins.translatable_read.TranslatableAPIReadMixin`.
    """

    translatable_overlay_fields: tuple[str, ...] = ()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        loc = display_locale_from_context(self.context)
        if not loc or not hasattr(instance, "get_translation_or_none"):
            return data
        trans = instance.get_translation_or_none(loc)
        if trans is None or trans.pk == instance.pk:
            return data
        for field in self.translatable_overlay_fields:
            if field in data:
                data[field] = getattr(trans, field)
        return data
