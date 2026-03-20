"""Seeder for Tenant model."""

from django.db import transaction
from tenants.models import Tenant
from .base import BaseSeeder


class TenantSeeder(BaseSeeder):
    """Create or retrieve the default tenant for seeding.

    This seeder must run first before all other seeders, as it establishes
    the tenant context that other seeders will use to create tenant-scoped data.
    """

    def __init__(self, verbose=True):
        """Initialize the seeder.

        Args:
            verbose: If True, print progress messages to stdout.
        """
        super().__init__(verbose=verbose)
        self.tenant = None

    def seed(self):
        """Create or retrieve the default tenant.

        Uses get_or_create() to ensure idempotency — safe to re-run multiple times.
        Returns the Tenant instance for use by downstream seeders.
        """
        self.log("Creating default tenant...")

        tenant, created = Tenant.objects.get_or_create(
            slug="default",
            defaults={
                "name": "Default",
                "is_active": True,
            },
        )

        if created:
            self.log(f"✓ Created tenant: {tenant.name} (slug={tenant.slug})")
        else:
            self.log(f"✓ Using existing tenant: {tenant.name} (slug={tenant.slug})")

        self.tenant = tenant

    def execute(self):
        """Execute the seeder within a transaction and return the tenant instance.

        Ensures atomicity: either the tenant is created/retrieved or an error is raised.

        Returns:
            Tenant: The default Tenant instance.
        """
        try:
            with transaction.atomic():
                self.seed()
                if self.verbose:
                    self.log("✓ Complete")
                return self.tenant
        except Exception as e:
            if self.verbose:
                self.log(f"✗ Failed: {str(e)}")
            raise
