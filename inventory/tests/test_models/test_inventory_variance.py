"""Unit tests for the InventoryVariance model (T-19)."""

from django.test import TestCase
from django.utils import timezone

from inventory.models import (
    InventoryVariance,
    VarianceResolution,
    VarianceType,
)

from ..factories import (
    create_cycle_count_line,
    create_inventory_cycle,
    create_inventory_variance,
    create_location,
    create_product,
    create_user,
)


class VarianceTypeDetectionTests(TestCase):
    """Test InventoryVariance.detect_variance_type static method."""

    def test_shortage_when_physical_less_than_system(self):
        result = InventoryVariance.detect_variance_type(100, 95)
        self.assertEqual(result, VarianceType.SHORTAGE)

    def test_surplus_when_physical_greater_than_system(self):
        result = InventoryVariance.detect_variance_type(100, 105)
        self.assertEqual(result, VarianceType.SURPLUS)

    def test_match_when_quantities_equal(self):
        result = InventoryVariance.detect_variance_type(100, 100)
        self.assertEqual(result, VarianceType.MATCH)

    def test_match_with_zero_quantities(self):
        result = InventoryVariance.detect_variance_type(0, 0)
        self.assertEqual(result, VarianceType.MATCH)

    def test_surplus_when_system_is_zero(self):
        result = InventoryVariance.detect_variance_type(0, 5)
        self.assertEqual(result, VarianceType.SURPLUS)

    def test_shortage_when_physical_is_zero(self):
        result = InventoryVariance.detect_variance_type(10, 0)
        self.assertEqual(result, VarianceType.SHORTAGE)

    def test_shortage_by_one(self):
        result = InventoryVariance.detect_variance_type(50, 49)
        self.assertEqual(result, VarianceType.SHORTAGE)

    def test_surplus_by_one(self):
        result = InventoryVariance.detect_variance_type(50, 51)
        self.assertEqual(result, VarianceType.SURPLUS)


class InventoryVarianceCreationTests(TestCase):
    """Test InventoryVariance creation and field defaults."""

    def setUp(self):
        self.location = create_location(name="Variance Warehouse")
        self.product = create_product(sku="VAR-001")
        self.cycle = create_inventory_cycle(name="Variance Cycle")
        self.count_line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=95,
        )

    def test_create_shortage_variance(self):
        variance = create_inventory_variance(
            cycle=self.cycle,
            count_line=self.count_line,
            product=self.product,
            location=self.location,
            system_quantity=100,
            physical_quantity=95,
        )
        self.assertEqual(variance.variance_type, VarianceType.SHORTAGE)
        self.assertEqual(variance.system_quantity, 100)
        self.assertEqual(variance.physical_quantity, 95)
        self.assertEqual(variance.variance_quantity, -5)
        self.assertIsNone(variance.resolution)
        self.assertIsNone(variance.adjustment_movement)
        self.assertIsNone(variance.resolved_by)
        self.assertIsNone(variance.resolved_at)
        self.assertEqual(variance.root_cause, "")

    def test_create_surplus_variance(self):
        location2 = create_location(name="Surplus Loc")
        product2 = create_product(sku="VAR-002")
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=product2,
            location=location2,
            system_quantity=50,
            counted_quantity=55,
        )
        variance = create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=product2,
            location=location2,
            system_quantity=50,
            physical_quantity=55,
        )
        self.assertEqual(variance.variance_type, VarianceType.SURPLUS)
        self.assertEqual(variance.variance_quantity, 5)

    def test_create_match_variance(self):
        location3 = create_location(name="Match Loc")
        product3 = create_product(sku="VAR-003")
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=product3,
            location=location3,
            system_quantity=75,
            counted_quantity=75,
        )
        variance = create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=product3,
            location=location3,
            system_quantity=75,
            physical_quantity=75,
        )
        self.assertEqual(variance.variance_type, VarianceType.MATCH)
        self.assertEqual(variance.variance_quantity, 0)


class InventoryVarianceResolutionTests(TestCase):
    """Test resolution workflow fields on InventoryVariance."""

    def setUp(self):
        self.location = create_location(name="Resolve Warehouse")
        self.product = create_product(sku="RES-001")
        self.cycle = create_inventory_cycle(name="Resolve Cycle")
        self.count_line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=90,
        )
        self.variance = create_inventory_variance(
            cycle=self.cycle,
            count_line=self.count_line,
            product=self.product,
            location=self.location,
            system_quantity=100,
            physical_quantity=90,
        )

    def test_resolve_as_accepted(self):
        user = create_user(username="resolver")
        now = timezone.now()
        self.variance.resolution = VarianceResolution.ACCEPTED
        self.variance.resolved_by = user
        self.variance.resolved_at = now
        self.variance.root_cause = "Shipping error"
        self.variance.save()

        self.variance.refresh_from_db()
        self.assertEqual(self.variance.resolution, VarianceResolution.ACCEPTED)
        self.assertEqual(self.variance.resolved_by, user)
        self.assertEqual(self.variance.root_cause, "Shipping error")

    def test_resolve_as_investigating(self):
        self.variance.resolution = VarianceResolution.INVESTIGATING
        self.variance.save()

        self.variance.refresh_from_db()
        self.assertEqual(self.variance.resolution, VarianceResolution.INVESTIGATING)

    def test_resolve_as_rejected(self):
        self.variance.resolution = VarianceResolution.REJECTED
        self.variance.root_cause = "Counting error by staff"
        self.variance.save()

        self.variance.refresh_from_db()
        self.assertEqual(self.variance.resolution, VarianceResolution.REJECTED)


class InventoryVarianceRelationshipTests(TestCase):
    """Test foreign key relationships and the OneToOne link to CycleCountLine."""

    def setUp(self):
        self.location = create_location(name="Rel Warehouse")
        self.product = create_product(sku="REL-001")
        self.cycle = create_inventory_cycle(name="Rel Cycle")

    def test_one_to_one_with_count_line(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=98,
        )
        variance = create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=self.product,
            location=self.location,
            system_quantity=100,
            physical_quantity=98,
        )
        self.assertEqual(line.variance_record, variance)
        self.assertEqual(variance.count_line, line)

    def test_variances_related_name_on_cycle(self):
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=50,
            counted_quantity=45,
        )
        create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=self.product,
            location=self.location,
            system_quantity=50,
            physical_quantity=45,
        )
        self.assertEqual(self.cycle.variances.count(), 1)

    def test_cascade_delete_on_cycle(self):
        """Deleting a cycle cascades to its variances."""
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=95,
        )
        create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=self.product,
            location=self.location,
            system_quantity=100,
            physical_quantity=95,
        )
        self.assertEqual(InventoryVariance.objects.count(), 1)
        self.cycle.delete()
        self.assertEqual(InventoryVariance.objects.count(), 0)

    def test_cascade_delete_on_count_line(self):
        """Deleting a count line cascades to its variance."""
        line = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product,
            location=self.location,
            system_quantity=100,
            counted_quantity=95,
        )
        create_inventory_variance(
            cycle=self.cycle,
            count_line=line,
            product=self.product,
            location=self.location,
            system_quantity=100,
            physical_quantity=95,
        )
        self.assertEqual(InventoryVariance.objects.count(), 1)
        line.delete()
        self.assertEqual(InventoryVariance.objects.count(), 0)


class InventoryVarianceStrTests(TestCase):
    """Test __str__ representation."""

    def test_str_for_shortage(self):
        location = create_location(name="Str Warehouse")
        product = create_product(sku="STR-001")
        cycle = create_inventory_cycle(name="Str Cycle")
        line = create_cycle_count_line(
            cycle=cycle,
            product=product,
            location=location,
            system_quantity=100,
            counted_quantity=95,
        )
        variance = create_inventory_variance(
            cycle=cycle,
            count_line=line,
            product=product,
            location=location,
            system_quantity=100,
            physical_quantity=95,
        )
        s = str(variance)
        self.assertIn("Shortage", s)
        self.assertIn("-5", s)

    def test_str_for_surplus(self):
        location = create_location(name="Str Warehouse 2")
        product = create_product(sku="STR-002")
        cycle = create_inventory_cycle(name="Str Cycle 2")
        line = create_cycle_count_line(
            cycle=cycle,
            product=product,
            location=location,
            system_quantity=50,
            counted_quantity=53,
        )
        variance = create_inventory_variance(
            cycle=cycle,
            count_line=line,
            product=product,
            location=location,
            system_quantity=50,
            physical_quantity=53,
        )
        s = str(variance)
        self.assertIn("Surplus", s)
        self.assertIn("+3", s)
