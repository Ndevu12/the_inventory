"""Unit tests for InventoryCycle model."""

from datetime import date, timedelta

from django.test import TestCase
from django.utils import timezone

from inventory.models import CycleStatus, InventoryCycle

from ..factories import create_inventory_cycle, create_location, create_user


# =====================================================================
# InventoryCycle — creation & defaults
# =====================================================================


class InventoryCycleCreationTests(TestCase):
    """Test InventoryCycle creation and field defaults."""

    def test_create_cycle(self):
        cycle = create_inventory_cycle(name="Annual Count")
        self.assertEqual(cycle.name, "Annual Count")
        self.assertEqual(cycle.scheduled_date, date.today())
        self.assertIsNotNone(cycle.pk)

    def test_default_status_is_scheduled(self):
        cycle = create_inventory_cycle()
        self.assertEqual(cycle.status, CycleStatus.SCHEDULED)

    def test_optional_fields_default_to_none_or_blank(self):
        cycle = create_inventory_cycle()
        self.assertIsNone(cycle.location)
        self.assertIsNone(cycle.started_at)
        self.assertIsNone(cycle.completed_at)
        self.assertIsNone(cycle.started_by)
        self.assertEqual(cycle.notes, "")

    def test_timestamps_set_on_create(self):
        cycle = create_inventory_cycle()
        self.assertIsNotNone(cycle.created_at)
        self.assertIsNotNone(cycle.updated_at)

    def test_create_with_location(self):
        location = create_location(name="Aisle A")
        cycle = create_inventory_cycle(location=location)
        self.assertEqual(cycle.location, location)

    def test_create_without_location_means_full_warehouse(self):
        cycle = create_inventory_cycle(location=None)
        self.assertIsNone(cycle.location)

    def test_scheduled_date_can_be_future(self):
        future = date.today() + timedelta(days=30)
        cycle = create_inventory_cycle(scheduled_date=future)
        self.assertEqual(cycle.scheduled_date, future)


# =====================================================================
# InventoryCycle — __str__
# =====================================================================


class InventoryCycleStrTests(TestCase):
    """Test InventoryCycle __str__ representation."""

    def test_str_contains_name_and_status(self):
        cycle = create_inventory_cycle(name="Q1 Full Count")
        text = str(cycle)
        self.assertIn("Q1 Full Count", text)
        self.assertIn("Scheduled", text)

    def test_str_reflects_status_change(self):
        cycle = create_inventory_cycle(name="Spot Check")
        cycle.status = CycleStatus.IN_PROGRESS
        cycle.save()
        self.assertIn("In Progress", str(cycle))


# =====================================================================
# InventoryCycle — status values
# =====================================================================


class CycleStatusTests(TestCase):
    """Test all CycleStatus choices can be persisted."""

    def test_all_status_values_accepted(self):
        for status_value, label in CycleStatus.choices:
            cycle = create_inventory_cycle(
                name=f"Cycle-{status_value}",
                status=status_value,
            )
            cycle.refresh_from_db()
            self.assertEqual(cycle.status, status_value)
            self.assertEqual(cycle.get_status_display(), label)

    def test_status_workflow_scheduled_to_in_progress(self):
        cycle = create_inventory_cycle()
        self.assertEqual(cycle.status, CycleStatus.SCHEDULED)

        cycle.status = CycleStatus.IN_PROGRESS
        cycle.started_at = timezone.now()
        cycle.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, CycleStatus.IN_PROGRESS)
        self.assertIsNotNone(cycle.started_at)

    def test_status_workflow_in_progress_to_completed(self):
        cycle = create_inventory_cycle(status=CycleStatus.IN_PROGRESS)
        cycle.status = CycleStatus.COMPLETED
        cycle.completed_at = timezone.now()
        cycle.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, CycleStatus.COMPLETED)
        self.assertIsNotNone(cycle.completed_at)

    def test_status_workflow_completed_to_reconciled(self):
        cycle = create_inventory_cycle(status=CycleStatus.COMPLETED)
        cycle.status = CycleStatus.RECONCILED
        cycle.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, CycleStatus.RECONCILED)

    def test_full_workflow_scheduled_through_reconciled(self):
        cycle = create_inventory_cycle()
        self.assertEqual(cycle.status, CycleStatus.SCHEDULED)

        cycle.status = CycleStatus.IN_PROGRESS
        cycle.started_at = timezone.now()
        cycle.save()

        cycle.status = CycleStatus.COMPLETED
        cycle.completed_at = timezone.now()
        cycle.save()

        cycle.status = CycleStatus.RECONCILED
        cycle.save()
        cycle.refresh_from_db()
        self.assertEqual(cycle.status, CycleStatus.RECONCILED)


# =====================================================================
# InventoryCycle — FK relationships
# =====================================================================


class InventoryCycleFKTests(TestCase):
    """Test foreign key relationships."""

    def test_location_set_null_on_delete(self):
        location = create_location(name="Temp Location")
        cycle = create_inventory_cycle(location=location)
        self.assertEqual(cycle.location, location)

        location.delete()
        cycle.refresh_from_db()
        self.assertIsNone(cycle.location)

    def test_started_by_user(self):
        user = create_user(username="counter")
        cycle = create_inventory_cycle(started_by=user)
        self.assertEqual(cycle.started_by, user)

    def test_started_by_set_null_on_delete(self):
        user = create_user(username="temp_user")
        cycle = create_inventory_cycle(started_by=user)
        user.delete()
        cycle.refresh_from_db()
        self.assertIsNone(cycle.started_by)


# =====================================================================
# InventoryCycle — ordering
# =====================================================================


class InventoryCycleOrderingTests(TestCase):
    """Test default ordering is -scheduled_date (newest first)."""

    def test_default_ordering_newest_scheduled_first(self):
        c1 = create_inventory_cycle(
            name="Older",
            scheduled_date=date.today() - timedelta(days=10),
        )
        c2 = create_inventory_cycle(
            name="Newer",
            scheduled_date=date.today(),
        )
        cycles = list(InventoryCycle.objects.all())
        self.assertEqual(cycles[0].pk, c2.pk)
        self.assertEqual(cycles[1].pk, c1.pk)
