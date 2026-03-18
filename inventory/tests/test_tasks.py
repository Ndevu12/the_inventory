"""Tests for Celery tasks and the sync-fallback dispatch helper.

All tests run with ``CELERY_TASK_ALWAYS_EAGER = True`` so tasks
execute synchronously in the test process — no broker required.
"""

from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from inventory.models import ReservationStatus
from inventory.models.job import AsyncJob, JobStatus
from inventory.tasks import (
    dispatch,
    expire_reservations,
    generate_report,
    process_bulk_operation,
)

from .factories import (
    create_location,
    create_product,
    create_reservation,
    create_stock_record,
    create_user,
)


class ExpireReservationsTaskTests(TestCase):
    """Test the expire_reservations Celery task."""

    def setUp(self):
        self.product = create_product(sku="TASK-001")
        self.warehouse = create_location(name="Task Warehouse")
        create_stock_record(product=self.product, location=self.warehouse, quantity=200)
        self.user = create_user(username="task_user")

    def test_expires_stale_reservations(self):
        stale = create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=10,
            status=ReservationStatus.PENDING,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        fresh = create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=5,
            status=ReservationStatus.PENDING,
            expires_at=timezone.now() + timedelta(hours=24),
        )

        result = expire_reservations()

        self.assertEqual(result["expired_count"], 1)

        stale.refresh_from_db()
        fresh.refresh_from_db()
        self.assertEqual(stale.status, ReservationStatus.EXPIRED)
        self.assertEqual(fresh.status, ReservationStatus.PENDING)

    def test_returns_zero_when_nothing_to_expire(self):
        result = expire_reservations()
        self.assertEqual(result["expired_count"], 0)

    def test_with_job_tracking(self):
        create_reservation(
            product=self.product,
            location=self.warehouse,
            quantity=5,
            status=ReservationStatus.PENDING,
            expires_at=timezone.now() - timedelta(hours=1),
        )

        job = AsyncJob.objects.create(
            task_name="inventory.tasks.expire_reservations",
            status=JobStatus.PENDING,
        )

        expire_reservations(_job_id=str(job.id))

        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.SUCCESS)
        self.assertEqual(job.result["expired_count"], 1)


class ProcessBulkOperationTaskTests(TestCase):
    """Test the process_bulk_operation Celery task."""

    def setUp(self):
        self.product = create_product(sku="BULK-001")
        self.from_loc = create_location(name="Src Warehouse")
        self.to_loc = create_location(name="Dst Warehouse")
        create_stock_record(product=self.product, location=self.from_loc, quantity=100)
        self.user = create_user(username="bulk_user")

    def test_bulk_transfer(self):
        result = process_bulk_operation(
            operation_type="transfer",
            operation_kwargs={
                "items": [{"product_id": self.product.pk, "quantity": 20}],
                "from_location_id": self.from_loc.pk,
                "to_location_id": self.to_loc.pk,
                "created_by_id": self.user.pk,
            },
        )
        self.assertEqual(result["operation"], "transfer")
        self.assertEqual(result["success_count"], 1)
        self.assertEqual(result["failure_count"], 0)

    def test_bulk_adjustment(self):
        result = process_bulk_operation(
            operation_type="adjustment",
            operation_kwargs={
                "items": [{"product_id": self.product.pk, "new_quantity": 50}],
                "location_id": self.from_loc.pk,
                "created_by_id": self.user.pk,
            },
        )
        self.assertEqual(result["operation"], "adjustment")
        self.assertEqual(result["success_count"], 1)

    def test_bulk_revalue(self):
        result = process_bulk_operation(
            operation_type="revalue",
            operation_kwargs={
                "items": [{"product_id": self.product.pk, "new_unit_cost": "15.00"}],
            },
        )
        self.assertEqual(result["operation"], "revalue")
        self.assertEqual(result["success_count"], 1)

    def test_unknown_operation_type_raises(self):
        with self.assertRaises(ValueError):
            process_bulk_operation(
                operation_type="unknown",
                operation_kwargs={},
            )


class GenerateReportTaskTests(TestCase):
    """Test the generate_report Celery task."""

    def setUp(self):
        self.product = create_product(sku="RPT-001", unit_cost=Decimal("25.00"))
        self.warehouse = create_location(name="Report Warehouse")
        create_stock_record(product=self.product, location=self.warehouse, quantity=40)

    def test_stock_valuation_report(self):
        result = generate_report(report_type="stock_valuation")
        self.assertIn("total_products", result)
        self.assertIn("total_value", result)

    def test_low_stock_report(self):
        result = generate_report(report_type="low_stock")
        self.assertIn("count", result)
        self.assertIn("skus", result)

    def test_overstock_report(self):
        result = generate_report(report_type="overstock")
        self.assertIn("count", result)

    def test_unknown_report_type_raises(self):
        with self.assertRaises(ValueError):
            generate_report(report_type="nonexistent")


class DispatchHelperTests(TestCase):
    """Test the dispatch() sync-fallback helper."""

    @patch("inventory.tasks._celery_available", return_value=False)
    def test_dispatch_runs_synchronously_when_celery_unavailable(self, _mock):
        product = create_product(sku="DISP-001")
        warehouse = create_location(name="Dispatch Warehouse")
        create_stock_record(product=product, location=warehouse, quantity=100)
        create_reservation(
            product=product,
            location=warehouse,
            quantity=10,
            status=ReservationStatus.PENDING,
            expires_at=timezone.now() - timedelta(hours=1),
        )
        user = create_user(username="dispatch_user")

        job = dispatch(expire_reservations, user=user)

        self.assertIsInstance(job, AsyncJob)
        self.assertEqual(job.status, JobStatus.SUCCESS)
        self.assertEqual(job.result["expired_count"], 1)
        self.assertEqual(job.created_by, user)
        self.assertEqual(job.task_name, "inventory.tasks.expire_reservations")

    @patch("inventory.tasks._celery_available", return_value=False)
    def test_dispatch_records_failure_on_exception(self, _mock):
        user = create_user(username="fail_user")

        job = dispatch(
            process_bulk_operation,
            kwargs={
                "operation_type": "unknown_bad",
                "operation_kwargs": {},
            },
            user=user,
        )

        self.assertEqual(job.status, JobStatus.FAILURE)
        self.assertIn("Unknown bulk operation type", job.error)


class AsyncJobModelTests(TestCase):
    """Test the AsyncJob lifecycle helpers."""

    def test_mark_started(self):
        job = AsyncJob.objects.create(task_name="test.task")
        job.mark_started()
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.STARTED)

    def test_mark_success(self):
        job = AsyncJob.objects.create(task_name="test.task")
        job.mark_success({"count": 42})
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.SUCCESS)
        self.assertEqual(job.result, {"count": 42})

    def test_mark_failure(self):
        job = AsyncJob.objects.create(task_name="test.task")
        job.mark_failure("something broke")
        job.refresh_from_db()
        self.assertEqual(job.status, JobStatus.FAILURE)
        self.assertEqual(job.error, "something broke")
