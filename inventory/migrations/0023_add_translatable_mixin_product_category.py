# Generated manually for I18N-03: TranslatableMixin on Product & Category.

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def _default_locale_pk(apps):
    """Match Wagtail default locale (0054_initial_locale runs before this migration)."""
    Locale = apps.get_model("wagtailcore", "Locale")
    from wagtail.coreutils import get_supported_content_language_variant

    code = get_supported_content_language_variant(settings.LANGUAGE_CODE)
    loc = Locale.objects.filter(language_code=code).first()
    if loc is not None:
        return loc.pk
    loc = Locale.objects.order_by("pk").first()
    if loc is None:
        raise RuntimeError(
            "Expected at least one wagtailcore.Locale after wagtailcore.0054_initial_locale."
        )
    return loc.pk


def backfill_translation_key_and_locale(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Category = apps.get_model("inventory", "Category")
    locale_pk = _default_locale_pk(apps)

    for row in Product.objects.all().iterator():
        if row.translation_key is None:
            row.translation_key = uuid.uuid4()
        if row.locale_id is None:
            row.locale_id = locale_pk
        row.save(update_fields=["translation_key", "locale_id"])

    for row in Category.objects.all().iterator():
        if row.translation_key is None:
            row.translation_key = uuid.uuid4()
        if row.locale_id is None:
            row.locale_id = locale_pk
        row.save(update_fields=["translation_key", "locale_id"])


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0022_alter_cyclecountline_tenant_and_more"),
        ("wagtailcore", "0054_initial_locale"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="product",
            name="unique_product_sku_per_tenant",
        ),
        migrations.RemoveConstraint(
            model_name="category",
            name="unique_category_slug_per_tenant",
        ),
        migrations.AddField(
            model_name="product",
            name="translation_key",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="category",
            name="translation_key",
            field=models.UUIDField(editable=False, null=True),
        ),
        migrations.AddField(
            model_name="product",
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
        migrations.AddField(
            model_name="category",
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
        migrations.RunPython(backfill_translation_key_and_locale, reverse_noop),
        migrations.AlterField(
            model_name="product",
            name="translation_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name="category",
            name="translation_key",
            field=models.UUIDField(default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name="product",
            name="locale",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="+",
                to="wagtailcore.locale",
                verbose_name="locale",
            ),
        ),
        migrations.AlterField(
            model_name="category",
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
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_inventory_product",
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("tenant", "sku", "locale"),
                name="unique_product_sku_per_tenant_locale",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("translation_key", "locale"),
                name="unique_translation_key_locale_inventory_category",
            ),
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=("tenant", "slug", "locale"),
                name="unique_category_slug_per_tenant_locale",
            ),
        ),
    ]
