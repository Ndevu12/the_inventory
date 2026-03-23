"""Management command to export tenant data to ZIP.

Usage::

    python manage.py export_tenant acme-corp
    python manage.py export_tenant 1 --output /tmp/acme.zip
    python manage.py export_tenant acme-corp --entity-types products,categories
    python manage.py export_tenant acme-corp --date-from 2025-01-01 --date-to 2025-03-31
"""

from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from tenants.models import Tenant
from tenants.services import TenantExportService


class Command(BaseCommand):
    help = "Export tenant data to a ZIP file (JSON + CSV)."

    def add_arguments(self, parser):
        parser.add_argument(
            "tenant",
            type=str,
            help="Tenant slug or numeric ID.",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=str,
            default=None,
            help="Output file path. Default: <slug>_export.zip in current directory.",
        )
        parser.add_argument(
            "--entity-types",
            type=str,
            default=None,
            help="Comma-separated entity types to export (default: all).",
        )
        parser.add_argument(
            "--date-from",
            type=str,
            default=None,
            help="Filter records from this date (YYYY-MM-DD).",
        )
        parser.add_argument(
            "--date-to",
            type=str,
            default=None,
            help="Filter records to this date (YYYY-MM-DD).",
        )

    def handle(self, *args, **options):
        tenant_id = options["tenant"]
        tenant = None
        if tenant_id.isdigit():
            tenant = Tenant.objects.filter(pk=int(tenant_id)).first()
        else:
            tenant = Tenant.objects.filter(slug=tenant_id).first()
        if not tenant:
            raise CommandError(f"Tenant '{tenant_id}' not found.")

        entity_types = None
        if options.get("entity_types"):
            entity_types = [x.strip() for x in options["entity_types"].split(",") if x.strip()]

        date_from = None
        date_to = None
        if options.get("date_from"):
            try:
                date_from = date.fromisoformat(options["date_from"])
            except ValueError:
                raise CommandError("date-from must be YYYY-MM-DD")
        if options.get("date_to"):
            try:
                date_to = date.fromisoformat(options["date_to"])
            except ValueError:
                raise CommandError("date-to must be YYYY-MM-DD")

        service = TenantExportService(
            tenant=tenant,
            entity_types=entity_types,
            date_from=date_from,
            date_to=date_to,
        )
        buffer = service.export_to_zip()

        base_dir = Path.cwd().resolve()

        user_output = options.get("output")
        if user_output:
            candidate_path = Path(user_output).expanduser().resolve()
            try:
                candidate_path.relative_to(base_dir)
            except ValueError:
                raise CommandError(
                    f"Output path '{user_output}' must be within the current directory."
                )
        else:
            # Sanitize slug further before using it in filename
            safe_slug = "".join(
                c for c in tenant.slug if c.isalnum() or c in ("-", "_")
            ) or "tenant"
            candidate_path = base_dir / f"{safe_slug}_export.zip"

        with candidate_path.open("wb") as f:
            f.write(buffer.getvalue())

        self.stdout.write(
            self.style.SUCCESS(f"Exported {tenant.name} to {candidate_path}")
        )
