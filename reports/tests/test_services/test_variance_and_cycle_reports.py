"""Tests for InventoryReportService variance and cycle history reporting."""

from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from inventory.models import CycleStatus, InventoryVariance, VarianceResolution, VarianceType
from inventory.tests.factories import (
    create_cycle_count_line,
    create_inventory_cycle,
    create_location,
    create_product,
    create_user,
)
from reports.services.inventory_reports import InventoryReportService


class VarianceReportSetupMixin:
    """Shared setUp that creates cycles with variances."""

    def setUp(self):
        self.service = InventoryReportService()
        self.warehouse = create_location(name="Warehouse")
        self.store = create_location(name="Store")
        self.user = create_user(username="counter")

        self.product_a = create_product(
            sku="VAR-A", name="Widget A",
            unit_cost=Decimal("10.00"),
        )
        self.product_b = create_product(
            sku="VAR-B", name="Widget B",
            unit_cost=Decimal("25.00"),
        )

        self.cycle = create_inventory_cycle(
            name="Q1 Count",
            status=CycleStatus.RECONCILED,
            scheduled_date=date(2026, 1, 15),
        )

        line_a = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product_a,
            location=self.warehouse,
            system_quantity=100,
            counted_quantity=95,
        )
        line_b = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product_b,
            location=self.warehouse,
            system_quantity=50,
            counted_quantity=55,
        )
        line_c = create_cycle_count_line(
            cycle=self.cycle,
            product=self.product_a,
            location=self.store,
            system_quantity=30,
            counted_quantity=30,
        )

        now = timezone.now()
        self.var_shortage = InventoryVariance.objects.create(
            cycle=self.cycle,
            count_line=line_a,
            product=self.product_a,
            location=self.warehouse,
            variance_type=VarianceType.SHORTAGE,
            system_quantity=100,
            physical_quantity=95,
            variance_quantity=-5,
            resolution=VarianceResolution.ACCEPTED,
            resolved_by=self.user,
            resolved_at=now,
        )
        self.var_surplus = InventoryVariance.objects.create(
            cycle=self.cycle,
            count_line=line_b,
            product=self.product_b,
            location=self.warehouse,
            variance_type=VarianceType.SURPLUS,
            system_quantity=50,
            physical_quantity=55,
            variance_quantity=5,
            resolution=VarianceResolution.INVESTIGATING,
            resolved_by=self.user,
            resolved_at=now,
        )
        self.var_match = InventoryVariance.objects.create(
            cycle=self.cycle,
            count_line=line_c,
            product=self.product_a,
            location=self.store,
            variance_type=VarianceType.MATCH,
            system_quantity=30,
            physical_quantity=30,
            variance_quantity=0,
            resolution=VarianceResolution.ACCEPTED,
            resolved_by=self.user,
            resolved_at=now,
        )


# =====================================================================
# Variance Report
# =====================================================================


class VarianceReportTests(VarianceReportSetupMixin, TestCase):
    """Test get_variance_report() filtering."""

    def test_returns_all_variances(self):
        qs = self.service.get_variance_report()
        self.assertEqual(qs.count(), 3)

    def test_filter_by_cycle_id(self):
        other_cycle = create_inventory_cycle(
            name="Q2 Count", status=CycleStatus.RECONCILED,
        )
        qs = self.service.get_variance_report(cycle_id=self.cycle.pk)
        self.assertEqual(qs.count(), 3)
        qs_other = self.service.get_variance_report(cycle_id=other_cycle.pk)
        self.assertEqual(qs_other.count(), 0)

    def test_filter_by_product_id(self):
        qs = self.service.get_variance_report(product_id=self.product_a.pk)
        self.assertEqual(qs.count(), 2)

    def test_filter_by_variance_type(self):
        qs = self.service.get_variance_report(variance_type=VarianceType.SHORTAGE)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().pk, self.var_shortage.pk)

    def test_filter_surplus(self):
        qs = self.service.get_variance_report(variance_type=VarianceType.SURPLUS)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().pk, self.var_surplus.pk)

    def test_filter_match(self):
        qs = self.service.get_variance_report(variance_type=VarianceType.MATCH)
        self.assertEqual(qs.count(), 1)

    def test_combined_filters(self):
        qs = self.service.get_variance_report(
            cycle_id=self.cycle.pk,
            product_id=self.product_a.pk,
            variance_type=VarianceType.SHORTAGE,
        )
        self.assertEqual(qs.count(), 1)

    def test_empty_result_with_nonexistent_product(self):
        qs = self.service.get_variance_report(product_id=99999)
        self.assertEqual(qs.count(), 0)


# =====================================================================
# Variance Summary
# =====================================================================


class VarianceSummaryTests(VarianceReportSetupMixin, TestCase):
    """Test get_variance_summary() aggregation."""

    def test_summary_all(self):
        summary = self.service.get_variance_summary()
        self.assertEqual(summary["total_variances"], 3)
        self.assertEqual(summary["net_variance"], 0)

        by_type = summary["by_type"]
        self.assertEqual(by_type[VarianceType.SHORTAGE]["count"], 1)
        self.assertEqual(by_type[VarianceType.SHORTAGE]["total_quantity"], -5)
        self.assertEqual(by_type[VarianceType.SURPLUS]["count"], 1)
        self.assertEqual(by_type[VarianceType.SURPLUS]["total_quantity"], 5)
        self.assertEqual(by_type[VarianceType.MATCH]["count"], 1)
        self.assertEqual(by_type[VarianceType.MATCH]["total_quantity"], 0)

    def test_summary_filtered_by_cycle(self):
        summary = self.service.get_variance_summary(cycle_id=self.cycle.pk)
        self.assertEqual(summary["total_variances"], 3)

    def test_summary_empty_cycle(self):
        other_cycle = create_inventory_cycle(
            name="Empty Cycle", status=CycleStatus.RECONCILED,
        )
        summary = self.service.get_variance_summary(cycle_id=other_cycle.pk)
        self.assertEqual(summary["total_variances"], 0)
        self.assertEqual(summary["net_variance"], 0)


# =====================================================================
# Cycle History
# =====================================================================


class CycleHistoryTests(VarianceReportSetupMixin, TestCase):
    """Test get_cycle_history() summary."""

    def test_returns_cycles(self):
        history = self.service.get_cycle_history()
        self.assertGreaterEqual(len(history), 1)

    def test_cycle_metadata(self):
        history = self.service.get_cycle_history()
        entry = next(c for c in history if c["id"] == self.cycle.pk)
        self.assertEqual(entry["name"], "Q1 Count")
        self.assertEqual(entry["status"], CycleStatus.RECONCILED)
        self.assertEqual(entry["status_display"], "Reconciled")
        self.assertEqual(entry["scheduled_date"], date(2026, 1, 15))

    def test_variance_statistics(self):
        history = self.service.get_cycle_history()
        entry = next(c for c in history if c["id"] == self.cycle.pk)
        self.assertEqual(entry["total_lines"], 3)
        self.assertEqual(entry["total_variances"], 3)
        self.assertEqual(entry["shortages"], 1)
        self.assertEqual(entry["surpluses"], 1)
        self.assertEqual(entry["matches"], 1)
        self.assertEqual(entry["net_variance"], 0)

    def test_ordering_most_recent_first(self):
        create_inventory_cycle(
            name="Older Count",
            scheduled_date=date(2025, 6, 1),
            status=CycleStatus.COMPLETED,
        )
        history = self.service.get_cycle_history()
        dates = [c["scheduled_date"] for c in history]
        self.assertEqual(dates, sorted(dates, reverse=True))

    def test_cycle_without_variances(self):
        scheduled = create_inventory_cycle(
            name="Future Count",
            scheduled_date=date(2026, 12, 1),
            status=CycleStatus.SCHEDULED,
        )
        history = self.service.get_cycle_history()
        entry = next(c for c in history if c["id"] == scheduled.pk)
        self.assertEqual(entry["total_variances"], 0)
        self.assertEqual(entry["shortages"], 0)
        self.assertEqual(entry["net_variance"], 0)
