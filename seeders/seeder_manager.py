"""Orchestrator for running all seeders in the correct order."""

from .tenant_seeder import TenantSeeder
from .user_seeder import UserSeeder
from .category_seeder import CategorySeeder
from .product_seeder import ProductSeeder
from .stock_location_seeder import StockLocationSeeder
from .stock_record_seeder import StockRecordSeeder
from .stock_movement_seeder import StockMovementSeeder
from .low_stock_seeder import LowStockSeeder


class SeederManager:
    """Manage and execute all seeders in dependency order with tenant context.

    Seeders are executed in a specific order to ensure dependencies are met:
    0. Tenant (creates or retrieves default tenant) — **runs first, always**
    1. Users (creates test users and assigns to tenant)
    2. Categories (needed by Products)
    3. Products (needed by StockRecords and StockMovements)
    4. StockLocations (needed by StockRecords and StockMovements)
    5. StockRecords (depends on Products and StockLocations)
    6. StockMovements (depends on Products and StockLocations)
    7. LowStockRecords (creates critical/low-stock scenarios for alerts)

    **Tenant-Scoped Seeding:**
    All seeders receive the tenant instance and scope created data to it. TenantSeeder
    runs first to establish the tenant context, then all other seeders call execute(tenant=tenant)
    to create data within that tenant's scope.
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
            ("Users", UserSeeder(verbose=verbose)),
            ("Categories", CategorySeeder(verbose=verbose)),
            ("Products", ProductSeeder(verbose=verbose)),
            ("Stock Locations", StockLocationSeeder(verbose=verbose)),
            ("Stock Records", StockRecordSeeder(verbose=verbose)),
            ("Stock Movements", StockMovementSeeder(verbose=verbose)),
            ("Low-Stock Scenarios", LowStockSeeder(verbose=verbose)),
        ]

    @staticmethod
    def _tenant_for_partial_seed(tenant=None):
        """Partial seed helpers need a tenant; default to slug ``default`` when omitted."""
        if tenant is not None:
            return tenant
        from tenants.models import Tenant

        t = Tenant.objects.filter(slug="default").first()
        if t is None:
            raise ValueError(
                "No tenant passed and no tenant with slug 'default' exists. "
                "Run a full seed, use --tenant, or create the default tenant first."
            )
        return t

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

    def seed(self, tenant=None):
        """Run all seeders in dependency order, with tenant-scoped data creation.

        Args:
            tenant: Optional Tenant instance to seed data into. If not provided,
                    TenantSeeder will create or retrieve the default tenant.

        Returns:
            dict: Result dictionary containing:
                - "tenant": The Tenant instance used for seeding
                - "objects_created": Dict of counts for each seeder
                  e.g., {"Categories": 5, "Products": 10, ...}
        """
        if self.clear_data:
            self.clear_all_data()
            print()

        if self.verbose:
            print("🌱 Seeding database with sample data...\n")

        from home.i18n_sync import refresh_i18n_settings_from_wagtail
        from seeders.wagtail_locale_seeder import ensure_default_wagtail_locales

        if self.verbose:
            print("📋 Ensuring Wagtail locales...")
        ensure_default_wagtail_locales(verbose=self.verbose)
        refresh_i18n_settings_from_wagtail()
        if self.verbose:
            print()

        # Step 1: Run TenantSeeder first to ensure tenant exists
        if tenant is None:
            if self.verbose:
                print("📋 Seeding Tenant...")
            tenant_seeder = TenantSeeder(verbose=self.verbose)
            tenant = tenant_seeder.execute()
            if self.verbose:
                print()
        else:
            if self.verbose:
                print(f"✓ Using provided tenant: {tenant.name} (slug={tenant.slug})\n")

        objects_created = {}

        # Step 2: Run all other seeders with tenant context
        for seeder_name, seeder in self.seeders:
            if self.verbose:
                print(f"📋 Seeding {seeder_name}...")
            seeder.execute(tenant=tenant)
            objects_created[seeder_name] = "✓"  # Placeholder for counts
            if self.verbose:
                print()

        if self.verbose:
            print("✅ Database seeding complete!")

        return {
            "tenant": tenant,
            "objects_created": objects_created,
        }

    def seed_users_only(self):
        """Seed only users (requires tenant to exist)."""
        from tenants.models import Tenant

        tenant = Tenant.objects.filter(slug="default").first()
        if not tenant:
            raise ValueError(
                "Default tenant does not exist. Run seed() first."
            )

        if self.verbose:
            print("🌱 Seeding Users...\n")
        self.seeders[0][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Users seeding complete!")

    def seed_categories_only(self, tenant=None):
        """Seed only categories."""
        tenant = self._tenant_for_partial_seed(tenant)
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
        self.seeders[1][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Categories seeding complete!")

    def seed_products_only(self, tenant=None):
        """Seed only products (requires categories to exist)."""
        tenant = self._tenant_for_partial_seed(tenant)
        if self.verbose:
            print("🌱 Seeding Products...\n")
        self.seeders[2][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Products seeding complete!")

    def seed_locations_only(self, tenant=None):
        """Seed only stock locations."""
        tenant = self._tenant_for_partial_seed(tenant)
        if self.verbose:
            print("🌱 Seeding Stock Locations...\n")
        self.seeders[3][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Stock Locations seeding complete!")

    def seed_stock_records_only(self, tenant=None):
        """Seed only stock records (requires products and locations)."""
        tenant = self._tenant_for_partial_seed(tenant)
        if self.verbose:
            print("🌱 Seeding Stock Records...\n")
        self.seeders[4][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Stock Records seeding complete!")

    def seed_movements_only(self, tenant=None):
        """Seed only stock movements (requires products and locations)."""
        tenant = self._tenant_for_partial_seed(tenant)
        if self.verbose:
            print("🌱 Seeding Stock Movements...\n")
        self.seeders[5][1].execute(tenant=tenant)
        if self.verbose:
            print("\n✅ Stock Movements seeding complete!")
