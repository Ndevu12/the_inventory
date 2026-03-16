"""Orchestrator for running all seeders in the correct order."""

from .category_seeder import CategorySeeder
from .product_seeder import ProductSeeder
from .stock_location_seeder import StockLocationSeeder
from .stock_record_seeder import StockRecordSeeder
from .stock_movement_seeder import StockMovementSeeder
from .low_stock_seeder import LowStockSeeder


class SeederManager:
    """Manage and execute all seeders in dependency order.

    Seeders are executed in a specific order to ensure dependencies are met:
    1. Categories (needed by Products)
    2. Products (needed by StockRecords and StockMovements)
    3. StockLocations (needed by StockRecords and StockMovements)
    4. StockRecords (depends on Products and StockLocations)
    5. StockMovements (depends on Products and StockLocations)
    6. LowStockRecords (creates critical/low-stock scenarios for alerts)
    """

    def __init__(self, verbose=True, clear_data=False):
        """Initialize the seeder manager.

        Args:
            verbose: If True, print progress messages.
            clear_data: If True, delete all existing data before seeding.
        """
        self.verbose = verbose
        self.clear_data = clear_data
        self.seeders = [
            ("Categories", CategorySeeder(verbose=verbose)),
            ("Products", ProductSeeder(verbose=verbose)),
            ("Stock Locations", StockLocationSeeder(verbose=verbose)),
            ("Stock Records", StockRecordSeeder(verbose=verbose)),
            ("Stock Movements", StockMovementSeeder(verbose=verbose)),
            ("Low-Stock Scenarios", LowStockSeeder(verbose=verbose)),
        ]

    def clear_all_data(self):
        """Delete all inventory data from the database."""
        from inventory.models import (
            Category,
            Product,
            StockLocation,
            StockRecord,
            StockMovement,
        )

        if self.verbose:
            print("🗑️  Clearing existing inventory data...")

        # Delete in reverse dependency order
        StockMovement.objects.all().delete()
        if self.verbose:
            print("  ✓ Deleted all StockMovements")

        StockRecord.objects.all().delete()
        if self.verbose:
            print("  ✓ Deleted all StockRecords")

        Product.objects.all().delete()
        if self.verbose:
            print("  ✓ Deleted all Products")

        StockLocation.objects.all().delete()
        if self.verbose:
            print("  ✓ Deleted all StockLocations")

        Category.objects.all().delete()
        if self.verbose:
            print("  ✓ Deleted all Categories")

    def seed(self):
        """Run all seeders in dependency order."""
        if self.clear_data:
            self.clear_all_data()
            print()

        if self.verbose:
            print("🌱 Seeding database with sample data...\n")

        for seeder_name, seeder in self.seeders:
            if self.verbose:
                print(f"📋 Seeding {seeder_name}...")
            seeder.execute()
            if self.verbose:
                print()

        if self.verbose:
            print("✅ Database seeding complete!")

    def seed_categories_only(self):
        """Seed only categories."""
        if self.clear_data:
            from inventory.models import (
                Category,
                Product,
                StockLocation,
                StockRecord,
                StockMovement,
            )

            StockMovement.objects.all().delete()
            StockRecord.objects.all().delete()
            Product.objects.all().delete()
            StockLocation.objects.all().delete()
            Category.objects.all().delete()

        if self.verbose:
            print("🌱 Seeding Categories...\n")
        self.seeders[0][1].execute()
        if self.verbose:
            print("\n✅ Categories seeding complete!")

    def seed_products_only(self):
        """Seed only products (requires categories to exist)."""
        if self.verbose:
            print("🌱 Seeding Products...\n")
        self.seeders[1][1].execute()
        if self.verbose:
            print("\n✅ Products seeding complete!")

    def seed_locations_only(self):
        """Seed only stock locations."""
        if self.verbose:
            print("🌱 Seeding Stock Locations...\n")
        self.seeders[2][1].execute()
        if self.verbose:
            print("\n✅ Stock Locations seeding complete!")

    def seed_stock_records_only(self):
        """Seed only stock records (requires products and locations)."""
        if self.verbose:
            print("🌱 Seeding Stock Records...\n")
        self.seeders[3][1].execute()
        if self.verbose:
            print("\n✅ Stock Records seeding complete!")

    def seed_movements_only(self):
        """Seed only stock movements (requires products and locations)."""
        if self.verbose:
            print("🌱 Seeding Stock Movements...\n")
        self.seeders[4][1].execute()
        if self.verbose:
            print("\n✅ Stock Movements seeding complete!")
