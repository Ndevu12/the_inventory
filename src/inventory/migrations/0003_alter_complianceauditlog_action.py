from django.db import migrations, models

import inventory.models.audit_action


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="complianceauditlog",
            name="action",
            field=models.CharField(
                choices=inventory.models.audit_action.AuditAction.choices,
                max_length=40,
            ),
        ),
    ]
