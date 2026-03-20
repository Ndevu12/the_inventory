"""Django management command to seed the database with sample data."""

from django.core.management.base import BaseCommand, CommandError
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

    def handle(self, *args, **options):
        """Execute the seed command."""
        try:
            verbose = not options.get("quiet", False)
            clear_data = options.get("clear", False)

            manager = SeederManager(verbose=verbose, clear_data=clear_data)
            models_to_seed = options.get("models", "").strip()

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
                # Seed all models
                result = manager.seed()
                if verbose:
                    self.stdout.write(
                        f"  Tenant: {result['tenant'].name} (slug={result['tenant'].slug})"
                    )

            self.stdout.write(
                self.style.SUCCESS("✅ Database seeding completed successfully!")
            )

        except Exception as e:
            raise CommandError(f"Seeding failed: {str(e)}")
