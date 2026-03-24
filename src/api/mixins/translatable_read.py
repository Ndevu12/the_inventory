"""Activate resolved language and scope read querysets to the tenant canonical locale."""

from django.utils import translation
from wagtail.models import TranslatableMixin

from api.language import (
    resolve_canonical_language_code,
    resolve_display_language_code,
    resolve_write_language_code,
    wagtail_locale_for_language,
)


class TranslatableAPIReadMixin:
    """For ``TranslatableMixin`` models: canonical rows on reads + display locale in context.

    - Read list/retrieve querysets are filtered to the tenant's **canonical** Wagtail locale
      (from ``tenant.preferred_language``) so product ids and stock FKs stay consistent.
    - ``?language=`` (then tenant default, then ``Accept-Language``) controls **display**
      strings via serializer context ``language`` (Django code), ``wagtail_display_locale``
      (Wagtail :class:`~wagtail.models.Locale`), and ``translation.activate``.
    """

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        tenant = self._get_current_tenant()
        display_code = resolve_display_language_code(request, tenant)
        canonical_code = resolve_canonical_language_code(tenant)
        write_code = resolve_write_language_code(request, tenant)
        self._api_display_language_code = display_code
        self._api_display_locale = wagtail_locale_for_language(display_code)
        self._api_canonical_locale = wagtail_locale_for_language(canonical_code)
        self._api_write_locale = wagtail_locale_for_language(write_code)
        translation.activate(display_code)

    def finalize_response(self, request, response, *args, **kwargs):
        translation.deactivate()
        return super().finalize_response(request, response, *args, **kwargs)

    def get_serializer_context(self):
        parent = super()
        get_ctx = getattr(parent, "get_serializer_context", None)
        ctx = get_ctx() if callable(get_ctx) else {}
        ctx["wagtail_display_locale"] = getattr(self, "_api_display_locale", None)
        ctx["language"] = getattr(self, "_api_display_language_code", None)
        ctx["wagtail_canonical_locale"] = getattr(self, "_api_canonical_locale", None)
        ctx["wagtail_write_locale"] = getattr(self, "_api_write_locale", None)
        return ctx

    def _read_list_uses_canonical_locale_only(self) -> bool:
        """One row per translation group on **list**; detail/actions keep full tenant scope."""
        if self.request.method not in ("GET", "HEAD"):
            return False
        return getattr(self, "action", None) == "list"

    def get_queryset(self):
        qs = super().get_queryset()
        if not self._read_list_uses_canonical_locale_only():
            return qs
        if not issubclass(qs.model, TranslatableMixin):
            return qs
        loc = getattr(self, "_api_canonical_locale", None)
        if loc is not None:
            qs = qs.filter(locale_id=loc.id)
        return qs
