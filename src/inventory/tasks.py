"""Celery tasks for async inventory operations.

Each public task follows the same pattern:
1. Accept only JSON-serialisable arguments (IDs, dicts, strings).
2. Create / update an :class:`AsyncJob` record to track progress.
3. Delegate real work to the existing service layer.
4. Return a JSON-serialisable result summary.

The module also exposes :func:`dispatch` — a helper that sends the task
to the Celery broker when available, or executes it synchronously as a
fallback.  Callers always get back an :class:`AsyncJob` instance.
"""

from __future__ import annotations

import logging
import traceback
import uuid

from celery import shared_task
from django.conf import settings

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Dispatcher: Celery-or-sync helper
# ------------------------------------------------------------------


def dispatch(task, *, args=None, kwargs=None, user=None):
    """Send *task* to the Celery broker, falling back to synchronous execution.

    Returns an :class:`inventory.models.job.AsyncJob` that the caller
    can serialise for the API response.
    """
    from inventory.models.job import AsyncJob, JobStatus

    job = AsyncJob.objects.create(
        task_name=task.name,
        status=JobStatus.PENDING,
        created_by=user,
    )

    task_kwargs = dict(kwargs or {})
    task_kwargs["_job_id"] = str(job.id)

    if _celery_available():
        result = task.apply_async(args=args, kwargs=task_kwargs)
        job.celery_task_id = result.id
        job.save(update_fields=["celery_task_id"])
    else:
        logger.info("Celery unavailable — running %s synchronously.", task.name)
        job.mark_started()
        try:
            ret = task(*(args or []), **task_kwargs)
            job.mark_success(ret)
        except Exception:
            job.mark_failure(traceback.format_exc())
            logger.exception("Sync fallback for %s failed.", task.name)

    return job


def _celery_available() -> bool:
    """Return True when the broker is reachable and ALWAYS_EAGER is off."""
    if getattr(settings, "CELERY_TASK_ALWAYS_EAGER", False):
        return False
    try:
        from the_inventory.celery import app
        conn = app.connection()
        conn.ensure_connection(max_retries=1, timeout=2)
        conn.close()
        return True
    except Exception:
        return False


# ------------------------------------------------------------------
# Shared helpers for task lifecycle
# ------------------------------------------------------------------


def _get_job(job_id_str: str | None):
    """Fetch the AsyncJob for this task invocation, if any."""
    if not job_id_str:
        return None
    from inventory.models.job import AsyncJob
    try:
        return AsyncJob.objects.get(pk=uuid.UUID(job_id_str))
    except (AsyncJob.DoesNotExist, ValueError):
        return None


def _run_with_job(job_id_str, fn):
    """Wrap *fn* in job lifecycle bookkeeping."""
    job = _get_job(job_id_str)
    if job:
        job.mark_started()
    try:
        result = fn()
        if job:
            job.mark_success(result)
        return result
    except Exception:
        if job:
            job.mark_failure(traceback.format_exc())
        raise


# ------------------------------------------------------------------
# Tasks
# ------------------------------------------------------------------


@shared_task(name="inventory.tasks.expire_reservations", bind=True, max_retries=3)
def expire_reservations(self, _job_id=None):
    """Periodic task: expire stale stock reservations.

    Replaces the management command ``expire_reservations`` for
    environments running Celery Beat.
    """
    def _do():
        from inventory.services.reservation import ReservationService
        count = ReservationService().expire_stale_reservations()
        return {"expired_count": count}

    return _run_with_job(_job_id, _do)


@shared_task(name="inventory.tasks.process_bulk_operation", bind=True, max_retries=2)
def process_bulk_operation(
    self,
    operation_type,
    operation_kwargs,
    _job_id=None,
):
    """Run a bulk stock operation asynchronously.

    Parameters
    ----------
    operation_type : str
        One of ``"transfer"``, ``"adjustment"``, ``"revalue"``.
    operation_kwargs : dict
        JSON-serialisable keyword arguments forwarded to the appropriate
        :class:`BulkStockService` method.  Foreign-key fields must be
        passed as integer IDs (``from_location_id``, ``to_location_id``,
        ``created_by_id``). Optional ``warehouse_id`` (int or null for
        retail-only) and ``retail_locations_only`` (bool) constrain
        resolved locations to the matching :class:`~inventory.models.stock.StockLocation`
        tree partition before the service runs.
    """
    def _do():
        from django.contrib.auth import get_user_model
        from inventory.models.stock import StockLocation
        from inventory.services.bulk import BulkStockService

        svc = BulkStockService()
        kw = dict(operation_kwargs)

        user_id = kw.pop("created_by_id", None)
        if user_id:
            kw["created_by"] = get_user_model().objects.get(pk=user_id)

        from inventory.utils.warehouse_scope import (
            WAREHOUSE_SCOPE_UNSPECIFIED,
            parse_report_warehouse_scope,
        )

        wh_key = kw.pop("warehouse_id", WAREHOUSE_SCOPE_UNSPECIFIED)
        retail_flag = bool(kw.pop("retail_locations_only", False))

        def _enforce_bulk_warehouse_scope(*locations):
            try:
                scope, wid = parse_report_warehouse_scope(
                    warehouse_id=wh_key,
                    retail_locations_only=retail_flag,
                )
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            if scope == "all":
                return
            for loc in locations:
                if loc is None:
                    continue
                if scope == "retail" and loc.warehouse_id is not None:
                    raise ValueError(
                        "Bulk operation location is not in the retail-only warehouse scope."
                    )
                if scope == "facility" and loc.warehouse_id != wid:
                    raise ValueError(
                        "Bulk operation location does not match the requested warehouse scope."
                    )

        if operation_type == "transfer":
            kw["from_location"] = StockLocation.objects.get(pk=kw.pop("from_location_id"))
            kw["to_location"] = StockLocation.objects.get(pk=kw.pop("to_location_id"))
            _enforce_bulk_warehouse_scope(kw["from_location"], kw["to_location"])
            result = svc.bulk_transfer(**kw)
        elif operation_type == "adjustment":
            kw["location"] = StockLocation.objects.get(pk=kw.pop("location_id"))
            _enforce_bulk_warehouse_scope(kw["location"])
            result = svc.bulk_adjustment(**kw)
        elif operation_type == "revalue":
            result = svc.bulk_revalue(**kw)
        else:
            raise ValueError(f"Unknown bulk operation type: {operation_type}")

        return {
            "operation": operation_type,
            "success_count": result.success_count,
            "failure_count": result.failure_count,
            "errors": result.errors,
        }

    return _run_with_job(_job_id, _do)


@shared_task(name="inventory.tasks.generate_report", bind=True, max_retries=2)
def generate_report(self, report_type, report_kwargs=None, _job_id=None):
    """Generate an inventory report asynchronously.

    Parameters
    ----------
    report_type : str
        One of ``"stock_valuation"``, ``"movement_summary"``,
        ``"low_stock"``, ``"overstock"``.
    report_kwargs : dict | None
        Keyword arguments forwarded to the report method. May include
        ``warehouse_id`` (int or JSON null for retail-only sites) and
        ``retail_locations_only`` (bool) for scope-aware inventory reports.
    """
    def _do():
        from reports.services.inventory_reports import InventoryReportService
        svc = InventoryReportService()
        raw_kw = dict(report_kwargs or {})
        scope_kw = {
            k: raw_kw[k]
            for k in ("warehouse_id", "retail_locations_only")
            if k in raw_kw
        }
        if "retail_locations_only" in scope_kw:
            scope_kw["retail_locations_only"] = bool(scope_kw["retail_locations_only"])

        if report_type == "stock_valuation":
            data = svc.get_valuation_summary(**scope_kw)
            data["total_value"] = str(data["total_value"])
            return data
        if report_type == "movement_summary":
            return svc.get_movement_summary(**scope_kw)
        if report_type == "low_stock":
            qs = svc.get_low_stock_products(**scope_kw)
            return {"count": qs.count(), "skus": list(qs.values_list("sku", flat=True)[:100])}
        if report_type == "overstock":
            qs = svc.get_overstock_products(**scope_kw)
            return {"count": qs.count(), "skus": list(qs.values_list("sku", flat=True)[:100])}
        raise ValueError(f"Unknown report type: {report_type}")

    return _run_with_job(_job_id, _do)


@shared_task(name="inventory.tasks.process_import", bind=True, max_retries=1)
def process_import(self, data_type, rows, tenant_id=None, user_id=None, _job_id=None):
    """Process a CSV/Excel import asynchronously.

    Parameters
    ----------
    data_type : str
        One of ``"products"``, ``"suppliers"``, ``"customers"``.
    rows : list[dict]
        Pre-parsed rows from the uploaded file.
    tenant_id : int | None
    user_id : int | None
    """
    def _do():
        from django.contrib.auth import get_user_model
        from inventory.imports.importers import CustomerImporter, ProductImporter, SupplierImporter
        from tenants.models import Tenant

        importer_map = {
            "products": ProductImporter,
            "suppliers": SupplierImporter,
            "customers": CustomerImporter,
        }
        cls = importer_map.get(data_type)
        if cls is None:
            raise ValueError(f"Unknown import data type: {data_type}")

        tenant = Tenant.objects.get(pk=tenant_id) if tenant_id else None
        user = get_user_model().objects.get(pk=user_id) if user_id else None

        importer = cls(rows=rows, tenant=tenant, user=user)
        result = importer.run()

        return {
            "data_type": data_type,
            "success": result.success,
            "created_count": result.created_count,
            "errors": result.errors,
        }

    return _run_with_job(_job_id, _do)
