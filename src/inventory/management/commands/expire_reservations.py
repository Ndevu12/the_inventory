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

    def handle(self, *args, **options):
        service = ReservationService()

        if options["dry_run"]:
            from django.utils import timezone

            from inventory.models.reservation import ReservationStatus, StockReservation

            count = StockReservation.objects.filter(
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
                expires_at__lte=timezone.now(),
            ).count()
            self.stdout.write(f"Would expire {count} reservation(s). (dry run)")
            return

        count = service.expire_stale_reservations()
        self.stdout.write(
            self.style.SUCCESS(f"Expired {count} reservation(s).")
        )
