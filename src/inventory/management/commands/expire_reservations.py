"""Management command to expire stale stock reservations.

Run periodically (e.g. via cron or Celery beat) to clean up
reservations that have passed their ``expires_at`` timestamp::

    python manage.py expire_reservations
    python manage.py expire_reservations --dry-run
"""

from django.core.management.base import BaseCommand

from inventory.services.reservation import ReservationService


class Command(BaseCommand):
    help = "Expire stock reservations that have passed their expires_at timestamp."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many reservations would expire without modifying data.",
        )
        parser.add_argument(
            "--tenant-id",
            type=int,
            default=None,
            help="Only expire reservations for this tenant (default: all tenants).",
        )

    def handle(self, *args, **options):
        service = ReservationService()

        if options["dry_run"]:
            from django.utils import timezone

            from inventory.models.reservation import ReservationStatus, StockReservation

            qs = StockReservation.objects.filter(
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
                expires_at__lte=timezone.now(),
            )
            if options["tenant_id"] is not None:
                qs = qs.filter(tenant_id=options["tenant_id"])
            count = qs.count()
            self.stdout.write(f"Would expire {count} reservation(s). (dry run)")
            return

        count = service.expire_stale_reservations(
            tenant_id=options["tenant_id"],
        )
        self.stdout.write(
            self.style.SUCCESS(f"Expired {count} reservation(s).")
        )
