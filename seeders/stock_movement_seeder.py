"""Seeder for StockMovement model."""

from django.utils import timezone
from datetime import timedelta
from inventory.models import Product, StockLocation, StockMovement, MovementType
from .base import BaseSeeder


class StockMovementSeeder(BaseSeeder):
    """Create sample stock movements (receives, issues, transfers)."""

    def seed(self):
        """Create realistic stock movement history."""
        self.log("Creating stock movements...")

        loc = self.canonical_locale

        # Get some products and locations (canonical locale rows — same as stock FKs)
        phone_1 = Product.objects.get(
            sku="PHONE-001", tenant=self.tenant, locale=loc,
        )
        phone_2 = Product.objects.get(
            sku="PHONE-002", tenant=self.tenant, locale=loc,
        )
        laptop_1 = Product.objects.get(
            sku="LAPTOP-001", tenant=self.tenant, locale=loc,
        )
        acc_1 = Product.objects.get(sku="ACC-001", tenant=self.tenant, locale=loc)
        chair = Product.objects.get(sku="CHAIR-001", tenant=self.tenant, locale=loc)

        bin_a1_1 = StockLocation.objects.get(name="Bin A1-1", tenant=self.tenant)
        bin_a1_2 = StockLocation.objects.get(name="Bin A1-2", tenant=self.tenant)
        bin_a2_1 = StockLocation.objects.get(name="Bin A2-1", tenant=self.tenant)
        bin_a2_2 = StockLocation.objects.get(name="Bin A2-2", tenant=self.tenant)
        shelf_a3 = StockLocation.objects.get(name="Shelf A3", tenant=self.tenant)
        shelf_b2 = StockLocation.objects.get(name="Shelf B2", tenant=self.tenant)
        overflow = StockLocation.objects.get(name="Overflow Section", tenant=self.tenant)

        now = timezone.now()

        # Historical movements
        movements = [
            # Receives
            {
                "product": phone_1,
                "movement_type": MovementType.RECEIVE,
                "quantity": 25,
                "to_location": bin_a1_1,
                "unit_cost": phone_1.unit_cost,
                "reference": "PO-2026-001",
                "notes": "Initial stock received from supplier",
            },
            {
                "product": phone_2,
                "movement_type": MovementType.RECEIVE,
                "quantity": 40,
                "to_location": bin_a1_2,
                "unit_cost": phone_2.unit_cost,
                "reference": "PO-2026-002",
                "notes": "Shipment from Samsung approved distributor",
            },
            {
                "product": laptop_1,
                "movement_type": MovementType.RECEIVE,
                "quantity": 14,
                "to_location": bin_a2_1,
                "unit_cost": laptop_1.unit_cost,
                "reference": "PO-2026-003",
                "notes": "MacBook Pro bulk order",
            },
            {
                "product": acc_1,
                "movement_type": MovementType.RECEIVE,
                "quantity": 200,
                "to_location": shelf_a3,
                "unit_cost": acc_1.unit_cost,
                "reference": "PO-2026-004",
                "notes": "USB-C cables from manufacturer",
            },
            # Issues (sales/outbound)
            {
                "product": phone_1,
                "movement_type": MovementType.ISSUE,
                "quantity": 5,
                "from_location": bin_a1_1,
                "unit_cost": phone_1.unit_cost,
                "reference": "SO-2026-0001",
                "notes": "Sold 5 units to retail partner",
            },
            {
                "product": chair,
                "movement_type": MovementType.ISSUE,
                "quantity": 3,
                "from_location": shelf_b2,
                "unit_cost": chair.unit_cost,
                "reference": "SO-2026-0002",
                "notes": "Office furniture order",
            },
            # Transfers (internal movements)
            {
                "product": phone_1,
                "movement_type": MovementType.TRANSFER,
                "quantity": 15,
                "from_location": bin_a1_1,
                "to_location": overflow,
                "unit_cost": phone_1.unit_cost,
                "reference": "TR-2026-001",
                "notes": "Moved excess stock to secondary warehouse",
            },
            {
                "product": laptop_1,
                "movement_type": MovementType.TRANSFER,
                "quantity": 6,
                "from_location": bin_a2_1,
                "to_location": bin_a2_2,
                "unit_cost": laptop_1.unit_cost,
                "reference": "TR-2026-002",
                "notes": "Balanced inventory between bins",
            },
            # Adjustments (inventory corrections)
            {
                "product": phone_2,
                "movement_type": MovementType.ADJUSTMENT,
                "quantity": 10,
                "from_location": bin_a1_2,
                "unit_cost": phone_2.unit_cost,
                "reference": "ADJ-2026-001",
                "notes": "Corrected stock discrepancy from cycle count",
            },
            {
                "product": acc_1,
                "movement_type": MovementType.ADJUSTMENT,
                "quantity": 5,
                "from_location": shelf_a3,
                "unit_cost": acc_1.unit_cost,
                "reference": "ADJ-2026-002",
                "notes": "Damaged units removed from inventory",
            },
        ]

        for idx, movement_data in enumerate(movements):
            # Check if movement already exists by reference
            if StockMovement.objects.filter(
                reference=movement_data["reference"],
                tenant=self.tenant,
            ).exists():
                continue

            # Vary timestamps
            timestamp = now - timedelta(days=10 - idx)
            movement = self.create_with_tenant(
                StockMovement,
                **movement_data,
                created_at=timestamp,
            )
            movement_type_label = movement.get_movement_type_display().title()
            self.log(f"  {movement.reference}: {movement.product.sku} ({movement_type_label})")

        self.log(f"Total movements created: {StockMovement.objects.filter(tenant=self.tenant).count()}")
