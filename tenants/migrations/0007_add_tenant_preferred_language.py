# Generated manually for I18N-05

from django.conf import settings
from django.db import migrations, models

# Mirror the_inventory.settings.base.LANGUAGES so the migration is stable if settings change.
_LANGUAGE_CHOICES = [
    ("en", "English"),
    ("fr", "Français"),
    ("sw", "Swahili"),
    ("rw", "Kinyarwanda"),
    ("es", "Español"),
]


def backfill_preferred_language_en(apps, schema_editor):
    codes = {code for code, _ in settings.LANGUAGES}
    if "en" not in codes:
        raise ValueError("settings.LANGUAGES must include 'en' as the tenant default.")
    Tenant = apps.get_model("tenants", "Tenant")
    Tenant.objects.all().update(preferred_language="en")


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0006_add_billing_notes"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="preferred_language",
            field=models.CharField(
                choices=_LANGUAGE_CHOICES,
                default="en",
                help_text="Default locale for this tenant (admin strings, API fallbacks).",
                max_length=5,
            ),
        ),
        migrations.RunPython(backfill_preferred_language_en, noop_reverse),
    ]
