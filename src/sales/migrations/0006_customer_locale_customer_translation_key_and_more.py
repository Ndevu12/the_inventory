# TranslatableMixin: locale + translation_key on Customer (I18N-04).

import uuid

import django.db.models.deletion
from django.db import migrations, models


def forwards_set_customer_locale(apps, schema_editor):
    Customer = apps.get_model("sales", "Customer")
    Locale = apps.get_model("wagtailcore", "Locale")
    locale = Locale.objects.order_by("pk").first()
    if locale is None:
        raise RuntimeError(
            "No wagtailcore.Locale rows. Run Wagtail migrations and create a default locale."
        )
    Customer.objects.filter(locale_id__isnull=True).update(locale_id=locale.pk)


def backwards_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0005_alter_customer_tenant_alter_dispatch_tenant_and_more"),
        ("wagtailcore", "0096_referenceindex_referenceindex_source_object_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="translation_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="customer",
            name="locale",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="wagtailcore.locale",
                verbose_name="locale",
            ),
        ),
        migrations.RunPython(forwards_set_customer_locale, backwards_noop),
        migrations.AlterField(
            model_name="customer",
            name="locale",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="wagtailcore.locale",
                verbose_name="locale",
            ),
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_sales_customer",
            ),
        ),
        migrations.RemoveConstraint(
            model_name="customer",
            name="unique_customer_code_per_tenant",
        ),
        migrations.AddConstraint(
            model_name="customer",
            constraint=models.UniqueConstraint(
                fields=("tenant", "code", "locale"),
                name="unique_customer_code_per_tenant_locale",
            ),
        ),
        migrations.AlterField(
            model_name="customer",
            name="translation_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
    ]
