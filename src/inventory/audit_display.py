"""Display helpers for compliance audit log API (scope labels, summaries)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from inventory.models.audit import AuditAction

if TYPE_CHECKING:
    from inventory.models.audit import ComplianceAuditLog

# Governance / platform lifecycle — excluded from tenant audit list by default.
PLATFORM_AUDIT_ACTIONS: frozenset[str] = frozenset(
    {
        AuditAction.TENANT_ACCESSED,
        AuditAction.TENANT_DEACTIVATED,
        AuditAction.TENANT_REACTIVATED,
        AuditAction.TENANT_LIMIT_OVERRIDDEN,
        AuditAction.IMPERSONATION_STARTED,
        AuditAction.IMPERSONATION_ENDED,
        AuditAction.TENANT_EXPORT,
    },
)

EVENT_SCOPE_OPERATIONAL = "operational"
EVENT_SCOPE_PLATFORM = "platform"


def event_scope_for_action(action: str) -> str:
    """Return API ``event_scope`` for a stored action value."""
    if action in PLATFORM_AUDIT_ACTIONS:
        return EVENT_SCOPE_PLATFORM
    return EVENT_SCOPE_OPERATIONAL


def build_audit_summary(entry: ComplianceAuditLog) -> str:
    """Short human-readable line from ``details``; falls back to action label."""
    details = entry.details if isinstance(entry.details, dict) else {}
    parts: list[str] = []

    q = details.get("quantity")
    if q is not None:
        parts.append(f"qty {q}")

    sku = details.get("sku")
    if sku:
        parts.append(str(sku))

    code = details.get("code")
    if code:
        parts.append(str(code))

    label = details.get("name")
    if label:
        parts.append(str(label))

    on = details.get("order_number")
    if on:
        parts.append(str(on))

    dnum = details.get("dispatch_number")
    if dnum:
        parts.append(str(dnum))

    grn = details.get("grn_number")
    if grn:
        parts.append(str(grn))

    st = details.get("status")
    if st:
        parts.append(str(st))

    wh_id = details.get("warehouse_id")
    if wh_id is not None:
        parts.append(f"warehouse #{wh_id}")

    fl = details.get("from_location")
    tl = details.get("to_location")
    if fl and tl:
        parts.append(f"{fl} → {tl}")
    elif fl:
        parts.append(f"from {fl}")
    elif tl:
        parts.append(f"to {tl}")

    loc = details.get("location")
    if loc and not (fl or tl):
        parts.append(str(loc))

    ref = details.get("reference")
    if ref:
        parts.append(f"ref {ref}")

    rid = details.get("reservation_id")
    if rid is not None:
        parts.append(f"reservation #{rid}")

    mid = details.get("movement_id")
    if mid is not None:
        parts.append(f"movement #{mid}")

    cn = details.get("cycle_name")
    if cn:
        parts.append(str(cn))

    uname = details.get("impersonated_username")
    if uname:
        parts.append(f"as {uname}")

    slug = details.get("tenant_slug")
    if slug:
        if entry.action == AuditAction.TENANT_ACCESSED:
            prev = details.get("previous_tenant_slug")
            if prev:
                parts.append(f"{prev} → {slug}")
            else:
                parts.append(str(slug))
        else:
            parts.append(str(slug))

    reason = details.get("reason")
    if reason:
        parts.append(str(reason))

    et = details.get("entity_types")
    if isinstance(et, list) and et:
        parts.append(", ".join(str(x) for x in et))

    if (
        details.get("max_users_override") is not None
        or details.get("max_products_override") is not None
    ):
        parts.append("limits updated")

    if parts:
        return "; ".join(parts)
    return entry.get_action_display()
