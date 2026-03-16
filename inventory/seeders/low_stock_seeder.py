"""Seeder for creating low-stock/runout scenarios."""

from django.db.models import F
from inventory.models import Product, StockLocation, StockRecord
from .base import BaseSeeder


class LowStockSeeder(BaseSeeder):
    """Create stock records with quantities at or below reorder points.
    
    This seeder intentionally creates low-stock conditions to demonstrate
    stock runout alerts in the admin dashboard.
    """

    def seed(self):
        """Create stock records that trigger low-stock alerts."""
        self.log("Creating low-stock scenarios...")

        # Critical items: quantity = 0 (completely out of stock)
        critical_items = [
            ("PHONE-001", "Bin A1-1"),  # iPhone 15 Pro - reorder_point: 5
            ("LAPTOP-001", "Bin A2-1"),  # MacBook Pro 16" - reorder_point: 3
        ]

        # Low stock items: quantity < reorder_point (below threshold)
        low_stock_items = [
            ("PHONE-002", "Bin A1-2", 2),  # Samsung Galaxy S24 - reorder_point: 5
            ("LAPTOP-002", "Bin A2-2", 1),  # Dell XPS 15 - reorder_point: 3
            ("ACC-001", "Shelf A3", 25),  # USB-C Cable - reorder_point: 50
            ("ACC-002", "Shelf A3", 30),  # Wireless Mouse - reorder_point: 50
            ("ACC-003", "Shelf A3", 40),  # Keyboard - reorder_point: 50
            ("DESK-001", "Shelf B1", 1),  # Desk A Regular - reorder_point: 3
            ("CHAIR-001", "Shelf B2", 2),  # Office Chair Standard - reorder_point: 5
        ]

        # Create critical (out of stock) records
        self.log("\n  Creating CRITICAL items (out of stock):")
        for sku, location_name in critical_items:
            try:
                product = Product.objects.get(sku=sku)
                location = StockLocation.objects.get(name=location_name)

                # Delete any existing record for this combo
                StockRecord.objects.filter(
                    product=product,
                    location=location
                ).delete()

                StockRecord.objects.create(
                    product=product,
                    location=location,
                    quantity=0,
                )
                deficit = product.reorder_point - 0
                self.log(
                    f"    🚨 {product.sku} @ {location.name}: 0 units "
                    f"(deficit: {deficit} units)"
                )
            except (Product.DoesNotExist, StockLocation.DoesNotExist) as e:
                self.log(f"    ⚠️  {sku} or location not found: {e}")

        # Create low-stock records
        self.log("\n  Creating LOW-STOCK items (below reorder point):")
        for sku, location_name, quantity in low_stock_items:
            try:
                product = Product.objects.get(sku=sku)
                location = StockLocation.objects.get(name=location_name)

                # Delete any existing record for this combo
                StockRecord.objects.filter(
                    product=product,
                    location=location
                ).delete()

                StockRecord.objects.create(
                    product=product,
                    location=location,
                    quantity=quantity,
                )
                deficit = product.reorder_point - quantity
                self.log(
                    f"    ⚠️  {product.sku} @ {location.name}: {quantity} units "
                    f"(below reorder point: {product.reorder_point}, deficit: {deficit} units)"
                )
            except (Product.DoesNotExist, StockLocation.DoesNotExist) as e:
                self.log(f"    ⚠️  {sku} or location not found: {e}")

        # Summary
        low_stock_count = StockRecord.objects.filter(
            product__reorder_point__gt=0,
            quantity__lte=F("product__reorder_point"),
        ).count()

        self.log(f"\n  Total items in low-stock alert status: {low_stock_count}")
