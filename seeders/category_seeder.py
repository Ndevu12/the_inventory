"""Seeder for Category model."""

from inventory.models import Category
from .base import BaseSeeder


class CategorySeeder(BaseSeeder):
    """Create sample product categories with a hierarchy."""

    def seed(self):
        """Create root and nested category nodes."""
        self.log("Creating categories...")

        # Root categories - check if exists first
        if not Category.objects.filter(slug="electronics", tenant=self.tenant).exists():
            electronics = self.add_root_with_tenant(
                Category,
                name="Electronics",
                slug="electronics",
                description="Electronic devices and accessories",
                is_active=True,
            )
            self.log(f"  Created: {electronics.name}")
        else:
            electronics = Category.objects.get(slug="electronics", tenant=self.tenant)

        if not Category.objects.filter(slug="furniture", tenant=self.tenant).exists():
            furniture = self.add_root_with_tenant(
                Category,
                name="Furniture",
                slug="furniture",
                description="Office and home furniture",
                is_active=True,
            )
            self.log(f"  Created: {furniture.name}")
        else:
            furniture = Category.objects.get(slug="furniture", tenant=self.tenant)

        if not Category.objects.filter(slug="office-supplies", tenant=self.tenant).exists():
            office_supplies = self.add_root_with_tenant(
                Category,
                name="Office Supplies",
                slug="office-supplies",
                description="Stationery and office materials",
                is_active=True,
            )
            self.log(f"  Created: {office_supplies.name}")
        else:
            office_supplies = Category.objects.get(slug="office-supplies", tenant=self.tenant)

        # Nested categories under Electronics
        if not Category.objects.filter(slug="phones", tenant=self.tenant).exists():
            phones = electronics.add_child(
                name="Phones",
                slug="phones",
                description="Mobile and smartphones",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {electronics.name} → {phones.name}")

        if not Category.objects.filter(slug="laptops", tenant=self.tenant).exists():
            laptops = electronics.add_child(
                name="Laptops",
                slug="laptops",
                description="Laptops and notebooks",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {electronics.name} → {laptops.name}")

        if not Category.objects.filter(slug="accessories", tenant=self.tenant).exists():
            accessories = electronics.add_child(
                name="Accessories",
                slug="accessories",
                description="Cables, chargers, adapters",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {electronics.name} → {accessories.name}")

        # Nested categories under Furniture
        if not Category.objects.filter(slug="desks", tenant=self.tenant).exists():
            desks = furniture.add_child(
                name="Desks",
                slug="desks",
                description="Office and computer desks",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {furniture.name} → {desks.name}")

        if not Category.objects.filter(slug="chairs", tenant=self.tenant).exists():
            chairs = furniture.add_child(
                name="Chairs",
                slug="chairs",
                description="Office and ergonomic chairs",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {furniture.name} → {chairs.name}")

        # Nested categories under Office Supplies
        if not Category.objects.filter(slug="pens-pencils", tenant=self.tenant).exists():
            pens = office_supplies.add_child(
                name="Pens & Pencils",
                slug="pens-pencils",
                description="Writing instruments",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {office_supplies.name} → {pens.name}")

        if not Category.objects.filter(slug="paper-notepads", tenant=self.tenant).exists():
            paper = office_supplies.add_child(
                name="Paper & Notepads",
                slug="paper-notepads",
                description="Paper, notebooks, and notepads",
                is_active=True,
                tenant=self.tenant,
            )
            self.log(f"  Created: {office_supplies.name} → {paper.name}")

        self.log(f"Total categories created: {Category.objects.filter(tenant=self.tenant).count()}")
