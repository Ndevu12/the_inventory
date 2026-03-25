"""Warehouse partition helpers for reports, tasks, and bulk operations."""

from __future__ import annotations

from django.db.models import Q

# Sentinel: omit warehouse scope to mean tenant-wide (all tree partitions).
WAREHOUSE_SCOPE_UNSPECIFIED = object()


def parse_report_warehouse_scope(
    *,
    warehouse_id: int | None | object = WAREHOUSE_SCOPE_UNSPECIFIED,
    retail_locations_only: bool = False,
) -> tuple[str, int | None]:
    """Normalise API/task kwargs into a report scope label and partition id.

    Returns one of:

    * ``("all", None)`` — include all locations for the tenant.
    * ``("retail", None)`` — only ``StockLocation`` rows with ``warehouse_id IS NULL``.
    * ``("facility", pk)`` — only locations in facility *pk*.

    Raises ``ValueError`` when ``retail_locations_only`` is combined with a
    concrete ``warehouse_id``.
    """
    unset = warehouse_id is WAREHOUSE_SCOPE_UNSPECIFIED
    if retail_locations_only:
        if not unset:
            raise ValueError(
                "Combine either retail_locations_only or warehouse_id, not both."
            )
        return "retail", None
    if unset:
        return "all", None
    if warehouse_id is None:
        return "retail", None
    return "facility", int(warehouse_id)


def stock_record_location_scope_q(
    scope: str,
    warehouse_id: int | None,
    *,
    product_aggregate: bool = False,
) -> Q | None:
    """Filter stock by location warehouse partition.

    When *product_aggregate* is True (default False), builds a :class:`~django.db.models.Q`
    for use in ``Sum("stock_records__quantity", filter=...)`` on ``Product`` querysets
    (lookups are prefixed with ``stock_records__``). Otherwise lookups target
    :class:`~inventory.models.stock.StockRecord` rows directly (e.g. ``location__warehouse_id``).
    """
    if scope == "all":
        return None
    prefix = "stock_records__" if product_aggregate else ""
    if scope == "retail":
        return Q(**{f"{prefix}location__warehouse_id__isnull": True})
    return Q(**{f"{prefix}location__warehouse_id": warehouse_id})


def movement_to_location_scope_q(
    scope: str,
    warehouse_id: int | None,
) -> Q | None:
    """Filter receive movements (``to_location``) by warehouse partition."""
    if scope == "all":
        return None
    if scope == "retail":
        return Q(to_location__warehouse_id__isnull=True)
    return Q(to_location__warehouse_id=warehouse_id)


def task_warehouse_id_from_kwargs(kw: dict) -> int | None | object:
    """Resolve ``warehouse_id`` for Celery JSON kwargs (missing key vs explicit null)."""
    if "warehouse_id" not in kw:
        return WAREHOUSE_SCOPE_UNSPECIFIED
    v = kw["warehouse_id"]
    if v is None:
        return None
    return int(v)


def report_scope_params_from_query(query_params) -> dict:
    """Build ``warehouse_id`` / ``retail_locations_only`` kwargs from HTTP query dict-like.

    * ``retail_locations_only=true|1`` → retail partition only.
    * ``warehouse_id=<int>`` → facility scope.
    * ``warehouse_id`` empty or omitted with no retail flag → tenant-wide (no extra kwargs).
    * Explicit ``warehouse_id=null`` string (optional) → retail partition.
    """
    retail = str(query_params.get("retail_locations_only", "")).lower() in (
        "1", "true", "yes",
    )
    if retail:
        return {"retail_locations_only": True}
    raw = query_params.get("warehouse_id")
    if raw is None or raw == "":
        return {}
    if isinstance(raw, str) and raw.lower() in ("null", "none"):
        return {"warehouse_id": None}
    return {"warehouse_id": int(raw)}
