# Generated migration for TS-06: Backfill and enforce non-nullable tenant
# This migration handles:
# 1. Backfill NULL tenant entries with the default tenant
# 2. Add tenant field to models that don't have it (StockReservation)
# 3. Alter existing tenant fields to be non-nullable

from django.db import migrations, models
import django.db.models.deletion


def backfill_default_tenant(apps, schema_editor):
    """Backfill all NULL tenant entries with the default tenant."""
    Tenant = apps.get_model("tenants", "Tenant")
    
    # Get or create the default tenant
    default_tenant, _ = Tenant.objects.get_or_create(
        slug="default",
        defaults={
            "name": "Default",
            "is_active": True,
        }
    )
    
    # Models that may have NULL tenant entries
    models_to_backfill = [
        "Category",
        "Product",
        "StockLocation",
        "StockRecord",
        "StockMovement",
        "StockLot",
        "StockReservation",
        "InventoryCycle",
        "ReservationRule",
    ]
    
    for model_name in models_to_backfill:
        try:
            Model = apps.get_model("inventory", model_name)
            # Only update records with NULL tenant
            null_count = Model.objects.filter(tenant__isnull=True).count()
            if null_count > 0:
                Model.objects.filter(tenant__isnull=True).update(tenant=default_tenant)
                print(f"✓ Backfilled {null_count} NULL tenant entries in {model_name}")
        except LookupError:
            # Model doesn't exist in this app state
            pass


def reverse_backfill(apps, schema_editor):
    """Reverse the backfill by setting tenant back to NULL.
    
    This is a no-op in practice because we're making the field non-nullable,
    so reverting would leave orphaned data. In a true rollback scenario,
    you would need to restore from a backup.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0020_alter_complianceauditlog_action"),
    ]

    operations = [
        # Step 1: Run backfill of NULL tenant entries
        migrations.RunPython(backfill_default_tenant, reverse_backfill),
        
        # Step 2: Alter all tenant fields to be non-nullable
        migrations.AlterField(
            model_name="category",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="stocklocation",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="stockrecord",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="stockmovement",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="stocklot",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="inventorycycle",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="reservationrule",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
        migrations.AlterField(
            model_name="stockreservation",
            name="tenant",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="%(app_label)s_%(class)s_set",
                to="tenants.tenant",
            ),
        ),
    ]
