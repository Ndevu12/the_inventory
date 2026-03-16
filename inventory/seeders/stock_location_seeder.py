"""Seeder for StockLocation model."""

from inventory.models import StockLocation
from .base import BaseSeeder


class StockLocationSeeder(BaseSeeder):
    """Create sample warehouse and storage locations."""

    def seed(self):
        """Create a hierarchical warehouse structure."""
        self.log("Creating stock locations...")

        # Main warehouse
        warehouse = StockLocation.add_root(
            name="Main Warehouse",
            description="Primary distribution warehouse",
            is_active=True,
        )
        self.log(f"Created: {warehouse.name}")

        # Aisles
        aisle_a = warehouse.add_child(
            name="Aisle A",
            description="High-value electronics section",
            is_active=True,
        )
        self.log(f"  Created: {warehouse.name} → {aisle_a.name}")

        aisle_b = warehouse.add_child(
            name="Aisle B",
            description="Furniture and large items",
            is_active=True,
        )
        self.log(f"  Created: {warehouse.name} → {aisle_b.name}")

        aisle_c = warehouse.add_child(
            name="Aisle C",
            description="Office supplies and consumables",
            is_active=True,
        )
        self.log(f"  Created: {warehouse.name} → {aisle_c.name}")

        # Shelves in Aisle A
        aisle_a_shelf_1 = aisle_a.add_child(
            name="Shelf A1",
            description="Phones and tablets",
            is_active=True,
        )
        self.log(f"    Created: {aisle_a.name} → {aisle_a_shelf_1.name}")

        aisle_a_shelf_2 = aisle_a.add_child(
            name="Shelf A2",
            description="Laptops and computers",
            is_active=True,
        )
        self.log(f"    Created: {aisle_a.name} → {aisle_a_shelf_2.name}")

        aisle_a_shelf_3 = aisle_a.add_child(
            name="Shelf A3",
            description="Accessories",
            is_active=True,
        )
        self.log(f"    Created: {aisle_a.name} → {aisle_a_shelf_3.name}")

        # Bins in Shelf A1
        bin_a1_1 = aisle_a_shelf_1.add_child(
            name="Bin A1-1",
            description="iPhone inventory",
            is_active=True,
        )
        self.log(f"      Created: {aisle_a_shelf_1.name} → {bin_a1_1.name}")

        bin_a1_2 = aisle_a_shelf_1.add_child(
            name="Bin A1-2",
            description="Samsung inventory",
            is_active=True,
        )
        self.log(f"      Created: {aisle_a_shelf_1.name} → {bin_a1_2.name}")

        # Bins in Shelf A2
        bin_a2_1 = aisle_a_shelf_2.add_child(
            name="Bin A2-1",
            description="MacBook inventory",
            is_active=True,
        )
        self.log(f"      Created: {aisle_a_shelf_2.name} → {bin_a2_1.name}")

        bin_a2_2 = aisle_a_shelf_2.add_child(
            name="Bin A2-2",
            description="Dell XPS inventory",
            is_active=True,
        )
        self.log(f"      Created: {aisle_a_shelf_2.name} → {bin_a2_2.name}")

        # Shelves in Aisle B
        aisle_b_shelf_1 = aisle_b.add_child(
            name="Shelf B1",
            description="Desks",
            is_active=True,
        )
        self.log(f"    Created: {aisle_b.name} → {aisle_b_shelf_1.name}")

        aisle_b_shelf_2 = aisle_b.add_child(
            name="Shelf B2",
            description="Chairs",
            is_active=True,
        )
        self.log(f"    Created: {aisle_b.name} → {aisle_b_shelf_2.name}")

        # Shelves in Aisle C
        aisle_c_shelf_1 = aisle_c.add_child(
            name="Shelf C1",
            description="Writing instruments",
            is_active=True,
        )
        self.log(f"    Created: {aisle_c.name} → {aisle_c_shelf_1.name}")

        aisle_c_shelf_2 = aisle_c.add_child(
            name="Shelf C2",
            description="Paper products",
            is_active=True,
        )
        self.log(f"    Created: {aisle_c.name} → {aisle_c_shelf_2.name}")

        # Secondary warehouse
        secondary = StockLocation.add_root(
            name="Secondary Warehouse",
            description="Backup and overflow storage",
            is_active=True,
        )
        self.log(f"Created: {secondary.name}")

        secondary_aisle = secondary.add_child(
            name="Overflow Section",
            description="General overflow storage",
            is_active=True,
        )
        self.log(f"  Created: {secondary.name} → {secondary_aisle.name}")

        self.log(f"Total locations created: {StockLocation.objects.count()}")
