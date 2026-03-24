# Add Arabic content locale (matches WAGTAIL_CONTENT_LANGUAGES / Next.js routing).

from django.db import migrations


def add_ar_locale(apps, schema_editor):
    Locale = apps.get_model("wagtailcore", "Locale")
    Locale.objects.get_or_create(language_code="ar")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0003_seed_wagtail_locales"),
    ]

    operations = [
        migrations.RunPython(add_ar_locale, noop_reverse),
    ]
