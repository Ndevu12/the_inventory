# Generated manually for TSS-07: enforce PurchaseOrderLine.tenant, unique (tenant, PO, product).

import django.db.models.deletion
from django.db import migrations, models


def backfill_purchaseorderline_tenant(apps, schema_editor):
    PurchaseOrderLine = apps.get_model("procurement", "PurchaseOrderLine")
    for line in PurchaseOrderLine.objects.filter(tenant__isnull=True).iterator():
        po = line.purchase_order
        if po.tenant_id:
            line.tenant_id = po.tenant_id
            line.save(update_fields=["tenant"])


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("procurement", "0003_alter_goodsreceivednote_grn_number_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_purchaseorderline_tenant,
            noop_reverse,
        ),
        migrations.AlterField(
            model_name="purchaseorderline",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="purchaseorderline",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="purchaseorderline",
            constraint=models.UniqueConstraint(
                fields=("tenant", "purchase_order", "product"),
                name="unique_purchaseorderline_tenant_po_product",
            ),
        ),
    ]
