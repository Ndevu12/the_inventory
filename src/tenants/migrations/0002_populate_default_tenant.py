"""Create a default tenant and assign all existing records to it.

This data migration ensures that every row created before multi-tenancy
was introduced has a valid tenant FK.  The default tenant is also the
target for single-tenant deployments that don't require multi-tenancy.
"""

from django.db import migrations

TENANT_AWARE_MODELS = [
    ("inventory", "Category"),
    ("inventory", "Product"),
    ("inventory", "StockLocation"),
    ("inventory", "StockRecord"),
    ("inventory", "StockMovement"),
    ("procurement", "Supplier"),
    ("procurement", "PurchaseOrder"),
    ("procurement", "PurchaseOrderLine"),
    ("procurement", "GoodsReceivedNote"),
    ("sales", "Customer"),
    ("sales", "SalesOrder"),
    ("sales", "SalesOrderLine"),
    ("sales", "Dispatch"),
]


def populate_default_tenant(apps, schema_editor):
    Tenant = apps.get_model("tenants", "Tenant")
    default_tenant, _ = Tenant.objects.get_or_create(
        slug="default",
        defaults={
            "name": "Default Organisation",
            "is_active": True,
            "subscription_plan": "free",
            "subscription_status": "active",
            "max_users": 100,
            "max_products": 10000,
        },
    )

    for app_label, model_name in TENANT_AWARE_MODELS:
        Model = apps.get_model(app_label, model_name)
        Model.objects.filter(tenant__isnull=True).update(tenant=default_tenant)


def reverse_populate(apps, schema_editor):
    for app_label, model_name in TENANT_AWARE_MODELS:
        Model = apps.get_model(app_label, model_name)
        Model.objects.all().update(tenant=None)


class Migration(migrations.Migration):

    dependencies = [
        ("tenants", "0001_initial"),
        ("inventory", "0008_category_tenant_product_tenant_stocklocation_tenant_and_more"),
        ("procurement", "0002_goodsreceivednote_tenant_purchaseorder_tenant_and_more"),
        ("sales", "0002_customer_tenant_dispatch_tenant_salesorder_tenant_and_more"),
    ]

    operations = [
        migrations.RunPython(populate_default_tenant, reverse_populate),
    ]
