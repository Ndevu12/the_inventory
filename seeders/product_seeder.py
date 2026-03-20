"""Seeder for Product, ProductImage, and ProductTag models."""

from decimal import Decimal
from inventory.models import Category, Product, UnitOfMeasure
from .base import BaseSeeder


class ProductSeeder(BaseSeeder):
    """Create sample products with images and tags."""

    def seed(self):
        """Create products across different categories."""
        self.log("Creating products...")

        # Get categories for the current tenant
        phones = Category.objects.get(slug="phones", tenant=self.tenant)
        laptops = Category.objects.get(slug="laptops", tenant=self.tenant)
        accessories = Category.objects.get(slug="accessories", tenant=self.tenant)
        desks = Category.objects.get(slug="desks", tenant=self.tenant)
        chairs = Category.objects.get(slug="chairs", tenant=self.tenant)
        pens = Category.objects.get(slug="pens-pencils", tenant=self.tenant)
        paper = Category.objects.get(slug="paper-notepads", tenant=self.tenant)

        products = [
            # Phones
            {
                "sku": "PHONE-001",
                "name": "iPhone 15 Pro",
                "category": phones,
                "description": "Premium smartphone with advanced camera system",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("999.99"),
                "reorder_point": 5,
                "is_active": True,
            },
            {
                "sku": "PHONE-002",
                "name": "Samsung Galaxy S24",
                "category": phones,
                "description": "Flagship Android phone with AI features",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("899.99"),
                "reorder_point": 5,
                "is_active": True,
            },
            # Laptops
            {
                "sku": "LAPTOP-001",
                "name": "MacBook Pro 16\"",
                "category": laptops,
                "description": "High-performance laptop for professionals",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("2499.00"),
                "reorder_point": 3,
                "is_active": True,
            },
            {
                "sku": "LAPTOP-002",
                "name": "Dell XPS 15",
                "category": laptops,
                "description": "Premium Windows laptop with OLED display",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("1899.00"),
                "reorder_point": 3,
                "is_active": True,
            },
            # Accessories
            {
                "sku": "ACC-001",
                "name": "USB-C Cable",
                "category": accessories,
                "description": "High-speed USB-C charging and data cable",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("15.99"),
                "reorder_point": 50,
                "is_active": True,
            },
            {
                "sku": "ACC-002",
                "name": "Wireless Mouse",
                "category": accessories,
                "description": "Ergonomic Bluetooth wireless mouse",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("49.99"),
                "reorder_point": 20,
                "is_active": True,
            },
            {
                "sku": "ACC-003",
                "name": "Screen Protector Pack",
                "category": accessories,
                "description": "Pack of 10 tempered glass screen protectors",
                "unit_of_measure": UnitOfMeasure.PACKS,
                "unit_cost": Decimal("19.99"),
                "reorder_point": 15,
                "is_active": True,
            },
            # Desks
            {
                "sku": "DESK-001",
                "name": "Standing Desk Pro",
                "category": desks,
                "description": "Electric adjustable height standing desk",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("699.99"),
                "reorder_point": 2,
                "is_active": True,
            },
            {
                "sku": "DESK-002",
                "name": "Gaming Desk RGB",
                "category": desks,
                "description": "Curved gaming desk with LED RGB lighting",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("399.00"),
                "reorder_point": 2,
                "is_active": True,
            },
            # Chairs
            {
                "sku": "CHAIR-001",
                "name": "Ergonomic Office Chair",
                "category": chairs,
                "description": "Premium ergonomic office chair with lumbar support",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("499.99"),
                "reorder_point": 3,
                "is_active": True,
            },
            {
                "sku": "CHAIR-002",
                "name": "Gaming Chair Black",
                "category": chairs,
                "description": "Racing-style gaming chair with reclining function",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("349.99"),
                "reorder_point": 3,
                "is_active": True,
            },
            # Pens & Pencils
            {
                "sku": "PEN-001",
                "name": "Ballpoint Pen Pack",
                "category": pens,
                "description": "Box of 50 quality ballpoint pens",
                "unit_of_measure": UnitOfMeasure.BOXES,
                "unit_cost": Decimal("9.99"),
                "reorder_point": 30,
                "is_active": True,
            },
            {
                "sku": "PEN-002",
                "name": "Mechanical Pencil Set",
                "category": pens,
                "description": "Set of 12 mechanical pencils with leads",
                "unit_of_measure": UnitOfMeasure.PACKS,
                "unit_cost": Decimal("12.99"),
                "reorder_point": 20,
                "is_active": True,
            },
            # Paper
            {
                "sku": "PAPER-001",
                "name": "A4 Paper Ream",
                "category": paper,
                "description": "Pack of 500 sheets of premium A4 paper",
                "unit_of_measure": UnitOfMeasure.PACKS,
                "unit_cost": Decimal("4.99"),
                "reorder_point": 50,
                "is_active": True,
            },
            {
                "sku": "PAPER-002",
                "name": "Notebook 100 Pages",
                "category": paper,
                "description": "Spiral bind notebook with 100 ruled pages",
                "unit_of_measure": UnitOfMeasure.PIECES,
                "unit_cost": Decimal("3.99"),
                "reorder_point": 25,
                "is_active": True,
            },
        ]

        for product_data in products:
            product, created = Product.objects.get_or_create(
                sku=product_data["sku"],
                tenant=self.tenant,
                defaults=product_data,
            )
            if created:
                self.log(f"  Created: {product.sku} - {product.name}")

        self.log(f"Total products created: {Product.objects.filter(tenant=self.tenant).count()}")
