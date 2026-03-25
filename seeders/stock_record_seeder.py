"""Seeder for StockRecord model."""

from inventory.models import Product, StockLocation, StockRecord
from .base import BaseSeeder


class StockRecordSeeder(BaseSeeder):
    """Create stock records linking products to locations with quantities."""

    def seed(self):
        """Create stock records across different locations."""
        self.log("Creating stock records...")

        # Stock distribution data: (product_sku, location_name, quantity)
        stock_distribution = [
            # Phones at various bins
            ("PHONE-001", "Bin A1-1", 25),
            ("PHONE-001", "Overflow Section", 15),
            ("PHONE-002", "Bin A1-2", 30),
            ("PHONE-002", "Bin A1-1", 10),
            # Laptops
            ("LAPTOP-001", "Bin A2-1", 8),
            ("LAPTOP-001", "Overflow Section", 5),
            ("LAPTOP-002", "Bin A2-2", 12),
            ("LAPTOP-002", "Bin A2-1", 6),
            # Accessories
            ("ACC-001", "Shelf A3", 200),
            ("ACC-002", "Shelf A3", 75),
            ("ACC-003", "Shelf A3", 120),
            # Desks
            ("DESK-001", "Shelf B1", 5),
            ("DESK-002", "Shelf B1", 8),
            # Chairs
            ("CHAIR-001", "Shelf B2", 12),
            ("CHAIR-002", "Shelf B2", 15),
            # Pens
            ("PEN-001", "Shelf C1", 50),
            ("PEN-002", "Shelf C1", 40),
            # Paper
            ("PAPER-001", "Shelf C2", 200),
            ("PAPER-002", "Shelf C2", 150),
            # Retail-only locations (warehouse=NULL on branch)
            ("PEN-001", "Retail — Sales Floor", 60),
            ("PAPER-001", "Retail — Stockroom", 100),
        ]

        loc = self.canonical_locale

        for sku, location_name, quantity in stock_distribution:
            product = Product.objects.get(
                sku=sku, tenant=self.tenant, locale=loc,
            )
            location = StockLocation.objects.get(name=location_name, tenant=self.tenant)

            # Use get_or_create for idempotency
            record, created = StockRecord.objects.get_or_create(
                product=product,
                location=location,
                tenant=self.tenant,
                defaults={"quantity": quantity},
            )
            if created:
                self.log(f"  {product.sku} @ {location.name}: {quantity} units")

        self.log(f"Total stock records created: {StockRecord.objects.filter(tenant=self.tenant).count()}")
