"""Unit tests for CycleCountLine model."""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from ..factories import (
    create_cycle_count_line,
    create_inventory_cycle,
    create_location,
    create_product,
    create_user,
)


class CycleCountLineCreationTests(TestCase):
    """Test CycleCountLine creation and field defaults."""

    def setUp(self):
        self.location = create_location(name="Warehouse A")
        self.product = create_product(sku="CYCLE-001")
        self.cycle = create_inventory_cycle(name="Q1 Count", location=self.location)

    def test_create_uncounted_line(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
        )
        self.assertEqual(line.system_quantity, 50)
        self.assertIsNone(line.counted_quantity)
        self.assertIsNone(line.counted_by)
        self.assertIsNone(line.counted_at)
        self.assertEqual(line.notes, "")

    def test_create_counted_line(self):
        user = create_user(username="counter")
        now = timezone.now()
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
            counted_quantity=48,
            counted_by=user,
            counted_at=now,
            notes="Two items damaged",
        )
        self.assertEqual(line.counted_quantity, 48)
        self.assertEqual(line.counted_by, user)
        self.assertEqual(line.counted_at, now)
        self.assertEqual(line.notes, "Two items damaged")

    def test_str_pending(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=10,
        )
        self.assertIn("pending", str(line))

    def test_str_counted(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=10,
            counted_quantity=8,
        )
        self.assertIn("counted=8", str(line))


class CycleCountLineVarianceTests(TestCase):
    """Test the variance computed property."""

    def setUp(self):
        self.location = create_location(name="Warehouse B")
        self.product = create_product(sku="VAR-001")
        self.cycle = create_inventory_cycle(name="Variance Count")

    def test_variance_returns_none_when_uncounted(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
        )
        self.assertIsNone(line.variance)

    def test_variance_positive_when_surplus(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=105,
        )
        self.assertEqual(line.variance, 5)

    def test_variance_negative_when_shortage(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=95,
        )
        self.assertEqual(line.variance, -5)

    def test_variance_zero_when_exact_match(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=100,
        )
        self.assertEqual(line.variance, 0)

    def test_variance_with_zero_system_quantity(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=0,
            counted_quantity=3,
        )
        self.assertEqual(line.variance, 3)

    def test_variance_with_negative_system_quantity(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=-5,
            counted_quantity=0,
        )
        self.assertEqual(line.variance, 5)


class CycleCountLineUniquenessTests(TestCase):
    """Test unique_together constraint on (cycle, product, location)."""

    def setUp(self):
        self.location = create_location(name="Warehouse C")
        self.product = create_product(sku="UNQ-001")
        self.cycle = create_inventory_cycle(name="Unique Count")

    def test_duplicate_cycle_product_location_raises(self):
        create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
        )
        with self.assertRaises(IntegrityError):
            create_cycle_count_line(
                cycle=self.cycle,
                product=self.product,
                location=self.location,
                system_quantity=60,
            )

    def test_same_product_different_location_allowed(self):
        location_b = create_location(name="Warehouse D")
        create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
        )
        line_b = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=location_b,
            system_quantity=30,
        )
        self.assertEqual(line_b.system_quantity, 30)

    def test_same_location_different_product_allowed(self):
        product_b = create_product(sku="UNQ-002", name="Other Product")
        create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
        )
        line_b = create_cycle_count_line(
            cycle=self.cycle,
            product=product_b,
            location=self.location,
            system_quantity=20,
        )
        self.assertEqual(line_b.system_quantity, 20)

    def test_same_product_location_different_cycle_allowed(self):
        cycle_b = create_inventory_cycle(name="Q2 Count")
        create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
        )
        line_b = create_cycle_count_line(
            cycle=cycle_b,
            product=self.product,
            location=self.location,
            system_quantity=55,
        )
        self.assertEqual(line_b.system_quantity, 55)


class CycleCountLineForeignKeyTests(TestCase):
    """Test foreign key relationships and cascading behavior."""

    def test_lines_related_name_on_cycle(self):
        location = create_location(name="FK Warehouse")
        product = create_product(sku="FK-001")
        cycle = create_inventory_cycle(name="FK Count")
        create_cycle_count_line(
            cycle=cycle,
            product=product,
            location=location,
            system_quantity=10,
        )
        self.assertEqual(cycle.lines.count(), 1)

    def test_cycle_count_lines_related_name_on_product(self):
        location = create_location(name="FK Warehouse 2")
        product = create_product(sku="FK-002")
        cycle = create_inventory_cycle(name="FK Count 2")
        create_cycle_count_line(
            cycle=cycle,
            product=product,
            location=location,
            system_quantity=10,
        )
        self.assertEqual(product.cycle_count_lines.count(), 1)

    def test_cascade_delete_on_cycle(self):
        """Deleting a cycle should delete its count lines."""
        location = create_location(name="Cascade Warehouse")
        product = create_product(sku="CASCADE-001")
        cycle = create_inventory_cycle(name="Cascade Count")
        create_cycle_count_line(
            cycle=cycle,
            product=product,
            location=location,
            system_quantity=10,
        )
        from inventory.models import CycleCountLine

        self.assertEqual(CycleCountLine.objects.count(), 1)
        cycle.delete()
        self.assertEqual(CycleCountLine.objects.count(), 0)
