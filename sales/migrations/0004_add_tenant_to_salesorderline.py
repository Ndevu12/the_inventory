# Generated manually for TSS-08: enforce SalesOrderLine.tenant, unique (tenant, SO, product).

import django.db.models.deletion
from django.db import migrations, models


def backfill_salesorderline_tenant(apps, schema_editor):
    SalesOrderLine = apps.get_model("sales", "SalesOrderLine")
    for line in SalesOrderLine.objects.filter(tenant__isnull=True).iterator():
        so = line.sales_order
        if so.tenant_id:
            line.tenant_id = so.tenant_id
            line.save(update_fields=["tenant"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sales", "0003_alter_customer_code_alter_dispatch_dispatch_number_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_salesorderline_tenant,
            noop_reverse,
        ),
        migrations.AlterField(
            model_name="salesorderline",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="salesorderline",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="salesorderline",
            constraint=models.UniqueConstraint(
                fields=("tenant", "sales_order", "product"),
                name="unique_salesorderline_tenant_so_product",
            ),
        ),
    ]
