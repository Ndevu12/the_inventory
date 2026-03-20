"""Django management command to seed the database with sample data."""

from django.core.management.base import BaseCommand, CommandError
from tenants.models import Tenant
from tenants.context import set_current_tenant, clear_current_tenant
from inventory.seeders import SeederManager


class Command(BaseCommand):
    """Seed the inventory database with sample data."""

    help = "Populate the inventory database with sample data for development and testing"

    def add_arguments(self, parser):
        """Add command-line arguments."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear all existing inventory data before seeding",
        )
        parser.add_argument(
            "--models",
            type=str,
            help=(
                "Comma-separated list of models to seed. "
                "Options: categories, products, locations, records, movements"
            ),
        )
        parser.add_argument(
            "--quiet",
            action="store_true",
            help="Suppress verbose output",
        )
        parser.add_argument(
            "--tenant",
            type=str,
            default=None,
            help="Seed for a specific tenant slug (e.g., 'acme-corp'). If omitted, uses Default tenant.",
        )
        parser.add_argument(
            "--create-default",
            action="store_true",
            help="Force create Default tenant if it doesn't exist. Only used when --tenant is not specified.",
        )

    def handle(self, *args, **options):
        """Execute the seed command."""
        try:
            verbose = not options.get("quiet", False)
            clear_data = options.get("clear", False)
            tenant_slug = options.get("tenant")
            create_default = options.get("create_default", False)

            # Resolve the tenant
            tenant = self._resolve_tenant(tenant_slug, create_default, verbose)

            # Set tenant context for all seeders
            set_current_tenant(tenant)

            try:
                manager = SeederManager(verbose=verbose, clear_data=clear_data)
                models_to_seed = (options.get("models") or "").strip()

                if models_to_seed:
                    # Seed specific models
                    models = [m.strip().lower() for m in models_to_seed.split(",")]
                    available_models = {
                        "categories": manager.seed_categories_only,
                        "products": manager.seed_products_only,
                        "locations": manager.seed_locations_only,
                        "records": manager.seed_stock_records_only,
                        "movements": manager.seed_movements_only,
                    }

                    invalid_models = set(models) - set(available_models.keys())
                    if invalid_models:
                        raise CommandError(
                            f"Invalid model(s): {', '.join(invalid_models)}. "
                            f"Available: {', '.join(available_models.keys())}"
                        )

                    for model in models:
                        available_models[model]()
                        if verbose:
                            self.stdout.write("")
                else:
                    # Seed all models with tenant context
                    manager.seed(tenant=tenant)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Database seeding completed successfully into "
                        f"tenant: {tenant.name} (slug={tenant.slug})"
                    )
                )

            finally:
                # Always clear tenant context after seeding
                clear_current_tenant()

        except Exception as e:
            raise CommandError(f"Seeding failed: {str(e)}")

    def _resolve_tenant(self, tenant_slug, create_default, verbose):
        """Resolve which tenant to seed into.

        Args:
            tenant_slug: Optional tenant slug to seed for. If None, uses Default tenant.
            create_default: If True, auto-create Default tenant if missing.
            verbose: If True, print progress messages.

        Returns:
            Tenant instance

        Raises:
            CommandError if tenant not found or if Default doesn't exist and create_default is False.
        """
        if tenant_slug:
            # Seed for specific tenant
            try:
                tenant = Tenant.objects.get(slug=tenant_slug)
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Using tenant: {tenant.name} (slug={tenant.slug})")
                    )
                return tenant
            except Tenant.DoesNotExist:
                raise CommandError(
                    f"Tenant with slug '{tenant_slug}' not found. "
                    f"Available tenants: {', '.join(Tenant.objects.values_list('slug', flat=True)) or 'none'}"
                )
        else:
            # Use/create Default tenant
            try:
                tenant = Tenant.objects.get(slug="default")
                if verbose:
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Using existing Default tenant")
                    )
                return tenant
            except Tenant.DoesNotExist:
                if not create_default:
                    raise CommandError(
                        "Default tenant does not exist. "
                        "Use --create-default to auto-create it, or use --tenant=<slug> to seed for a specific tenant."
                    )
                # Create Default tenant (use get_or_create to avoid race conditions)
                if verbose:
                    self.stdout.write("Creating Default tenant...")
                tenant, created = Tenant.objects.get_or_create(
                    slug="default",
                    defaults={
                        "name": "Default",
                        "is_active": True,
                    }
                )
                if verbose:
                    if created:
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Created Default tenant")
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Using existing Default tenant")
                        )
                return tenant
