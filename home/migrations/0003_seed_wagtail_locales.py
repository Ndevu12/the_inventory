# I18N-13: Ensure Wagtail Locale rows for app-supported languages (repeatable deploys).

from django.db import migrations

# Historical bootstrap (repeatable deploys). Default set also in
# ``seeders.wagtail_locale_seeder.DEFAULT_LOCALE_CODES``; runtime languages
# follow Wagtail Settings → Locales (see ``home.i18n_sync``).
SUPPORTED_LOCALES = (
    "en",
    "fr",
    "sw",
    "rw",
    "es",
)


def seed_locales(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    for code in SUPPORTED_LOCALES:
        Locale.objects.get_or_create(language_code=code)


def seed_locales_reverse(apps, schema_editor):
    # Locales may be referenced by translatable models; do not delete on unapply.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0002_create_homepage"),
        ("wagtailcore", "0054_initial_locale"),
    ]

    operations = [
        migrations.RunPython(seed_locales, seed_locales_reverse),
    ]
