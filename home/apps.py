from django.apps import AppConfig
from django.db.models.signals import post_delete, post_migrate, post_save


class HomeConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "home"

    def ready(self):
        from home.i18n_sync import refresh_i18n_settings_from_wagtail

        def _refresh_on_locale_change(sender, instance, **kwargs):
            refresh_i18n_settings_from_wagtail()

        def _refresh_on_post_migrate(sender, **kwargs):
            if sender.label not in {"home", "wagtailcore"}:
                return
            refresh_i18n_settings_from_wagtail()

        post_migrate.connect(
            _refresh_on_post_migrate,
            dispatch_uid="home.refresh_i18n_post_migrate",
        )

        try:
            from wagtail.models import Locale

            post_save.connect(
                _refresh_on_locale_change,
                sender=Locale,
                dispatch_uid="home.refresh_i18n_locale_save",
            )
            post_delete.connect(
                _refresh_on_locale_change,
                sender=Locale,
                dispatch_uid="home.refresh_i18n_locale_delete",
            )
        except LookupError:
            pass

        refresh_i18n_settings_from_wagtail()
