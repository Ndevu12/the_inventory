# Align nullable tenant columns on procurement models with TimeStampedModel (non-null).

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("procurement", "0004_add_tenant_to_purchaseorderline"),
    ]

    operations = [
        migrations.AlterField(
            model_name="goodsreceivednote",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="purchaseorder",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="supplier",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
    ]
