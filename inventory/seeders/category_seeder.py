"""Seeder for Category model."""

from inventory.models import Category
from .base import BaseSeeder


class CategorySeeder(BaseSeeder):
    """Create sample product categories with a hierarchy."""

    def seed(self):
        """Create root and nested category nodes."""
        self.log("Creating categories...")

        # Root categories
        electronics = Category.add_root(
            name="Electronics",
            slug="electronics",
            description="Electronic devices and accessories",
            is_active=True,
        )
        self.log(f"  Created: {electronics.name}")

        furniture = Category.add_root(
            name="Furniture",
            slug="furniture",
            description="Office and home furniture",
            is_active=True,
        )
        self.log(f"  Created: {furniture.name}")

        office_supplies = Category.add_root(
            name="Office Supplies",
            slug="office-supplies",
            description="Stationery and office materials",
            is_active=True,
        )
        self.log(f"  Created: {office_supplies.name}")

        # Nested categories under Electronics
        phones = electronics.add_child(
            name="Phones",
            slug="phones",
            description="Mobile and smartphones",
            is_active=True,
        )
        self.log(f"  Created: {electronics.name} → {phones.name}")

        laptops = electronics.add_child(
            name="Laptops",
            slug="laptops",
            description="Laptops and notebooks",
            is_active=True,
        )
        self.log(f"  Created: {electronics.name} → {laptops.name}")

        accessories = electronics.add_child(
            name="Accessories",
            slug="accessories",
            description="Cables, chargers, adapters",
            is_active=True,
        )
        self.log(f"  Created: {electronics.name} → {accessories.name}")

        # Nested categories under Furniture
        desks = furniture.add_child(
            name="Desks",
            slug="desks",
            description="Office and computer desks",
            is_active=True,
        )
        self.log(f"  Created: {furniture.name} → {desks.name}")

        chairs = furniture.add_child(
            name="Chairs",
            slug="chairs",
            description="Office and ergonomic chairs",
            is_active=True,
        )
        self.log(f"  Created: {furniture.name} → {chairs.name}")

        # Nested categories under Office Supplies
        pens = office_supplies.add_child(
            name="Pens & Pencils",
            slug="pens-pencils",
            description="Writing instruments",
            is_active=True,
        )
        self.log(f"  Created: {office_supplies.name} → {pens.name}")

        paper = office_supplies.add_child(
            name="Paper & Notepads",
            slug="paper-notepads",
            description="Paper, notebooks, and notepads",
            is_active=True,
        )
        self.log(f"  Created: {office_supplies.name} → {paper.name}")

        self.log(f"Total categories created: {Category.objects.count()}")
