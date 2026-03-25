"""Tenant services — export logic, tenant creation, and related operations."""

from __future__ import annotations

import csv
import io
import json
import zipfile
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from tenants.models import (
    INVITATION_EXPIRY_DAYS,
    InvitationStatus,
    SubscriptionPlan,
    Tenant,
    TenantInvitation,
    TenantMembership,
    TenantRole,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractBaseUser

User = get_user_model()


def create_tenant_with_owner(
    *,
    name: str,
    slug: str,
    subscription_plan: str = SubscriptionPlan.FREE,
    max_users: int | None = None,
    max_products: int | None = None,
    is_active: bool = True,
    branding_site_name: str = "",
    branding_primary_color: str = "",
    # Owner: either existing user, new user with password, or invitation
    owner_user: AbstractBaseUser | None = None,
    owner_username: str | None = None,
    owner_email: str | None = None,
    owner_password: str | None = None,
    send_owner_invitation: bool = False,
    invited_by: AbstractBaseUser | None = None,
) -> tuple[Tenant, TenantInvitation | None]:
    """Create a tenant and optionally assign an owner.

    Shared logic for the createtenant command and Wagtail create form.

    Owner resolution:
    - If owner_user is provided: use that user as owner (create TenantMembership).
    - If owner_username is provided and user exists: use that user.
    - If owner_username is provided and user does not exist:
      - If owner_password: create user with password, TenantMembership.
      - If send_owner_invitation: create TenantInvitation (role=OWNER); no user yet.
    - Owner assignment does not grant Django/Wagtail staff; tenant access is via
      TenantMembership only (platform operators are provisioned separately).

    Returns:
        Tuple of (tenant, invitation_or_none). Invitation is set when
        send_owner_invitation=True; caller should send the invitation email.
    """
    with transaction.atomic():
        tenant = Tenant.objects.create(
            name=name.strip(),
            slug=slug,
            is_active=is_active,
            subscription_plan=subscription_plan,
            branding_site_name=(branding_site_name or "")[:255],
            branding_primary_color=(branding_primary_color or "")[:7],
            **({"max_users": max_users} if max_users is not None else {}),
            **({"max_products": max_products} if max_products is not None else {}),
        )

        invitation: TenantInvitation | None = None
        user: AbstractBaseUser | None = None

        if owner_user is not None:
            user = owner_user
        elif owner_username:
            try:
                user = User.objects.get(username=owner_username)
            except User.DoesNotExist:
                if send_owner_invitation and owner_email:
                    # Create invitation; no user yet
                    invitation = TenantInvitation.objects.create(
                        tenant=tenant,
                        email=owner_email,
                        role=TenantRole.OWNER,
                        status=InvitationStatus.PENDING,
                        invited_by=invited_by,
                        expires_at=timezone.now() + timezone.timedelta(days=INVITATION_EXPIRY_DAYS),
                    )
                elif owner_password:
                    user = User.objects.create_user(
                        username=owner_username,
                        email=owner_email or "",
                        password=owner_password,
                    )
                else:
                    raise ValueError(
                        "For new owner user, provide owner_password or send_owner_invitation with owner_email."
                    )

        if user is not None:
            membership, created = TenantMembership.objects.get_or_create(
                tenant=tenant,
                user=user,
                defaults={
                    "role": TenantRole.OWNER,
                    "is_active": True,
                    "is_default": True,
                },
            )
            if not created:
                membership.role = TenantRole.OWNER
                membership.is_active = True
                membership.is_default = True
                membership.save()

        return tenant, invitation


def send_invitation_email(invitation: TenantInvitation) -> None:
    """Send invitation email. Best-effort; fails silently in development."""
    from django.conf import settings as django_settings
    from django.core.mail import send_mail

    frontend_base = getattr(django_settings, "FRONTEND_URL", "http://localhost:3000")
    accept_url = f"{frontend_base}/accept-invitation/{invitation.token}"

    inviter_display = "A platform admin"
    if invitation.invited_by:
        inviter_display = (
            invitation.invited_by.get_full_name() or invitation.invited_by.username
        )

    subject = f"You've been invited to {invitation.tenant.name}"
    message = (
        f"Hi,\n\n{inviter_display} has invited you to join \"{invitation.tenant.name}\" "
        f"as {invitation.get_role_display()}.\n\n"
        f"Click the link below to accept:\n{accept_url}\n\n"
        f"This invitation expires on "
        f"{invitation.expires_at.strftime('%B %d, %Y at %H:%M UTC')}.\n\n"
        f"If you didn't expect this invitation, you can safely ignore it."
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[invitation.email],
            fail_silently=True,
        )
    except Exception:
        pass


def _json_serializer(obj: Any) -> Any:
    """Handle Decimal, date, datetime for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat() if obj else None
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _model_to_dict_flat(model_instance) -> dict[str, Any]:
    """Convert a model instance to a flat dict suitable for JSON/CSV export."""
    from django.forms.models import model_to_dict

    data = model_to_dict(
        model_instance,
        exclude=["tenant"],
        fields=[f.name for f in model_instance._meta.get_fields() if not f.many_to_many and not f.one_to_many],
    )
    result = {}
    for key, value in data.items():
        if value is None:
            result[key] = None
        elif isinstance(value, Decimal):
            result[key] = float(value)
        elif isinstance(value, (datetime, date)):
            result[key] = value.isoformat() if value else None
        elif hasattr(value, "pk"):
            result[f"{key}_id"] = value.pk
        else:
            result[key] = value
    return result


class TenantExportService:
    """Export tenant data to ZIP (JSON + CSV)."""

    ENTITY_TYPES = [
        "categories",
        "products",
        "locations",
        "stock_records",
        "stock_movements",
        "stock_lots",
        "suppliers",
        "purchase_orders",
        "goods_received_notes",
        "customers",
        "sales_orders",
        "dispatches",
    ]

    def __init__(
        self,
        tenant: Tenant,
        *,
        entity_types: list[str] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ):
        self.tenant = tenant
        self.entity_types = set(entity_types) if entity_types else set(self.ENTITY_TYPES)
        self.date_from = date_from
        self.date_to = date_to

    def _date_filter(self, qs: QuerySet, field: str = "created_at") -> QuerySet:
        """Apply optional date range filter."""
        if self.date_from:
            qs = qs.filter(**{f"{field}__date__gte": self.date_from})
        if self.date_to:
            qs = qs.filter(**{f"{field}__date__lte": self.date_to})
        return qs

    def _export_categories(self) -> tuple[list[dict], list[list[str]]]:
        """Export categories as JSON-serializable and CSV rows."""
        from inventory.models import Category

        qs = Category.objects.filter(tenant=self.tenant).order_by("path")
        qs = self._date_filter(qs)

        rows = []
        for cat in qs:
            rows.append({
                "id": cat.pk,
                "name": cat.name,
                "slug": cat.slug,
                "description": cat.description,
                "is_active": cat.is_active,
                "path": getattr(cat, "path", ""),
                "depth": getattr(cat, "depth", 0),
                "created_at": cat.created_at.isoformat() if cat.created_at else None,
                "updated_at": cat.updated_at.isoformat() if cat.updated_at else None,
            })
        csv_rows = [["id", "name", "slug", "description", "is_active", "path", "depth", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_products(self) -> tuple[list[dict], list[list[str]]]:
        """Export products (description as plain text)."""
        from inventory.models import Product

        qs = Product.objects.filter(tenant=self.tenant).select_related("category").order_by("sku")
        qs = self._date_filter(qs)

        rows = []
        for p in qs:
            rows.append({
                "id": p.pk,
                "sku": p.sku,
                "name": p.name,
                "description": str(p.description) if p.description else "",
                "category_id": p.category_id,
                "unit_of_measure": p.unit_of_measure,
                "unit_cost": float(p.unit_cost) if p.unit_cost is not None else None,
                "reorder_point": p.reorder_point,
                "tracking_mode": p.tracking_mode,
                "is_active": p.is_active,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "updated_at": p.updated_at.isoformat() if p.updated_at else None,
            })
        csv_rows = [["id", "sku", "name", "description", "category_id", "unit_of_measure", "unit_cost", "reorder_point", "tracking_mode", "is_active", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_locations(self) -> tuple[list[dict], list[list[str]]]:
        """Export stock locations."""
        from inventory.models import StockLocation

        qs = StockLocation.objects.filter(tenant=self.tenant).order_by("path")
        qs = self._date_filter(qs)

        rows = []
        for loc in qs:
            rows.append({
                "id": loc.pk,
                "name": loc.name,
                "description": loc.description,
                "is_active": loc.is_active,
                "max_capacity": loc.max_capacity,
                "path": getattr(loc, "path", ""),
                "depth": getattr(loc, "depth", 0),
                "created_at": loc.created_at.isoformat() if loc.created_at else None,
                "updated_at": loc.updated_at.isoformat() if loc.updated_at else None,
            })
        csv_rows = [["id", "name", "description", "is_active", "max_capacity", "path", "depth", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_stock_records(self) -> tuple[list[dict], list[list[str]]]:
        """Export stock records."""
        from inventory.models import StockRecord

        qs = StockRecord.objects.filter(product__tenant=self.tenant).select_related("product", "location")
        qs = self._date_filter(qs)

        rows = []
        for r in qs:
            rows.append({
                "id": r.pk,
                "product_id": r.product_id,
                "location_id": r.location_id,
                "quantity": r.quantity,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            })
        csv_rows = [["id", "product_id", "location_id", "quantity", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_stock_movements(self) -> tuple[list[dict], list[list[str]]]:
        """Export stock movements."""
        from inventory.models import StockMovement

        qs = StockMovement.objects.filter(product__tenant=self.tenant).select_related(
            "product", "from_location", "to_location"
        )
        qs = self._date_filter(qs)

        rows = []
        for m in qs:
            rows.append({
                "id": m.pk,
                "product_id": m.product_id,
                "from_location_id": m.from_location_id,
                "to_location_id": m.to_location_id,
                "quantity": m.quantity,
                "unit_cost": float(m.unit_cost) if m.unit_cost is not None else None,
                "movement_type": m.movement_type,
                "reference": m.reference,
                "notes": m.notes,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            })
        csv_rows = [["id", "product_id", "from_location_id", "to_location_id", "quantity", "unit_cost", "movement_type", "reference", "notes", "created_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_stock_lots(self) -> tuple[list[dict], list[list[str]]]:
        """Export stock lots."""
        from inventory.models import StockLot

        qs = StockLot.objects.filter(tenant=self.tenant).select_related("product", "supplier", "purchase_order")
        qs = self._date_filter(qs)

        rows = []
        for lot in qs:
            rows.append({
                "id": lot.pk,
                "product_id": lot.product_id,
                "lot_number": lot.lot_number,
                "serial_number": lot.serial_number,
                "manufacturing_date": lot.manufacturing_date.isoformat() if lot.manufacturing_date else None,
                "expiry_date": lot.expiry_date.isoformat() if lot.expiry_date else None,
                "quantity_received": lot.quantity_received,
                "quantity_remaining": lot.quantity_remaining,
                "supplier_id": lot.supplier_id,
                "purchase_order_id": lot.purchase_order_id,
                "received_date": lot.received_date.isoformat() if lot.received_date else None,
                "is_active": lot.is_active,
                "created_at": lot.created_at.isoformat() if lot.created_at else None,
                "updated_at": lot.updated_at.isoformat() if lot.updated_at else None,
            })
        csv_rows = [["id", "product_id", "lot_number", "serial_number", "manufacturing_date", "expiry_date", "quantity_received", "quantity_remaining", "supplier_id", "purchase_order_id", "received_date", "is_active", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_suppliers(self) -> tuple[list[dict], list[list[str]]]:
        """Export suppliers."""
        from procurement.models import Supplier

        qs = Supplier.objects.filter(tenant=self.tenant).order_by("code")
        qs = self._date_filter(qs)

        rows = []
        for s in qs:
            rows.append({
                "id": s.pk,
                "code": s.code,
                "name": s.name,
                "contact_name": s.contact_name,
                "email": s.email,
                "phone": s.phone,
                "address": s.address,
                "lead_time_days": s.lead_time_days,
                "payment_terms": s.payment_terms,
                "is_active": s.is_active,
                "notes": s.notes,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            })
        csv_rows = [["id", "code", "name", "contact_name", "email", "phone", "address", "lead_time_days", "payment_terms", "is_active", "notes", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_purchase_orders(self) -> tuple[list[dict], list[dict]]:
        """Export purchase orders with lines."""
        from procurement.models import PurchaseOrder

        qs = PurchaseOrder.objects.filter(tenant=self.tenant).select_related("supplier").prefetch_related("lines")
        qs = self._date_filter(qs)

        rows = []
        for po in qs:
            lines = []
            for line in po.lines.all():
                lines.append({
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_cost": float(line.unit_cost),
                })
            rows.append({
                "id": po.pk,
                "order_number": po.order_number,
                "supplier_id": po.supplier_id,
                "status": po.status,
                "order_date": po.order_date.isoformat() if po.order_date else None,
                "expected_delivery_date": po.expected_delivery_date.isoformat() if po.expected_delivery_date else None,
                "notes": po.notes,
                "lines": lines,
                "created_at": po.created_at.isoformat() if po.created_at else None,
                "updated_at": po.updated_at.isoformat() if po.updated_at else None,
            })
        csv_rows = [["id", "order_number", "supplier_id", "status", "order_date", "expected_delivery_date", "notes", "created_at", "updated_at"]]
        for r in rows:
            line_data = len(r.get("lines", []))
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]] + [str(line_data)])
        csv_rows[0].append("line_count")
        return rows, csv_rows

    def _export_grns(self) -> tuple[list[dict], list[list[str]]]:
        """Export goods received notes."""
        from procurement.models import GoodsReceivedNote

        qs = GoodsReceivedNote.objects.filter(tenant=self.tenant).select_related("purchase_order", "location")
        qs = self._date_filter(qs)

        rows = []
        for g in qs:
            rows.append({
                "id": g.pk,
                "grn_number": g.grn_number,
                "purchase_order_id": g.purchase_order_id,
                "received_date": g.received_date.isoformat() if g.received_date else None,
                "location_id": g.location_id,
                "notes": g.notes,
                "is_processed": g.is_processed,
                "created_at": g.created_at.isoformat() if g.created_at else None,
                "updated_at": g.updated_at.isoformat() if g.updated_at else None,
            })
        csv_rows = [["id", "grn_number", "purchase_order_id", "received_date", "location_id", "notes", "is_processed", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_customers(self) -> tuple[list[dict], list[list[str]]]:
        """Export customers."""
        from sales.models import Customer

        qs = Customer.objects.filter(tenant=self.tenant).order_by("code")
        qs = self._date_filter(qs)

        rows = []
        for c in qs:
            rows.append({
                "id": c.pk,
                "code": c.code,
                "name": c.name,
                "contact_name": c.contact_name,
                "email": c.email,
                "phone": c.phone,
                "address": c.address,
                "is_active": c.is_active,
                "notes": c.notes,
                "created_at": c.created_at.isoformat() if c.created_at else None,
                "updated_at": c.updated_at.isoformat() if c.updated_at else None,
            })
        csv_rows = [["id", "code", "name", "contact_name", "email", "phone", "address", "is_active", "notes", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def _export_sales_orders(self) -> tuple[list[dict], list[dict]]:
        """Export sales orders with lines."""
        from sales.models import SalesOrder

        qs = SalesOrder.objects.filter(tenant=self.tenant).select_related("customer").prefetch_related("lines")
        qs = self._date_filter(qs)

        rows = []
        for so in qs:
            lines = []
            for line in so.lines.all():
                lines.append({
                    "product_id": line.product_id,
                    "quantity": line.quantity,
                    "unit_price": float(line.unit_price),
                })
            rows.append({
                "id": so.pk,
                "order_number": so.order_number,
                "customer_id": so.customer_id,
                "status": so.status,
                "order_date": so.order_date.isoformat() if so.order_date else None,
                "notes": so.notes,
                "lines": lines,
                "created_at": so.created_at.isoformat() if so.created_at else None,
                "updated_at": so.updated_at.isoformat() if so.updated_at else None,
            })
        csv_rows = [["id", "order_number", "customer_id", "status", "order_date", "notes", "created_at", "updated_at", "line_count"]]
        for r in rows:
            line_count = len(r.get("lines", []))
            csv_rows.append([str(r.get(k, "")) for k in ["id", "order_number", "customer_id", "status", "order_date", "notes", "created_at", "updated_at"]] + [str(line_count)])
        return rows, csv_rows

    def _export_dispatches(self) -> tuple[list[dict], list[list[str]]]:
        """Export dispatches."""
        from sales.models import Dispatch

        qs = Dispatch.objects.filter(tenant=self.tenant).select_related("sales_order", "from_location")
        qs = self._date_filter(qs)

        rows = []
        for d in qs:
            rows.append({
                "id": d.pk,
                "dispatch_number": d.dispatch_number,
                "sales_order_id": d.sales_order_id,
                "dispatch_date": d.dispatch_date.isoformat() if d.dispatch_date else None,
                "from_location_id": d.from_location_id,
                "notes": d.notes,
                "is_processed": d.is_processed,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            })
        csv_rows = [["id", "dispatch_number", "sales_order_id", "dispatch_date", "from_location_id", "notes", "is_processed", "created_at", "updated_at"]]
        for r in rows:
            csv_rows.append([str(r.get(k, "")) for k in csv_rows[0]])
        return rows, csv_rows

    def export_to_zip(self) -> io.BytesIO:
        """Build ZIP containing JSON and CSV files. Returns BytesIO."""
        buffer = io.BytesIO()
        slug = self.tenant.slug
        exported_at = timezone.now().isoformat()

        handlers = {
            "categories": self._export_categories,
            "products": self._export_products,
            "locations": self._export_locations,
            "stock_records": self._export_stock_records,
            "stock_movements": self._export_stock_movements,
            "stock_lots": self._export_stock_lots,
            "suppliers": self._export_suppliers,
            "purchase_orders": self._export_purchase_orders,
            "goods_received_notes": self._export_grns,
            "customers": self._export_customers,
            "sales_orders": self._export_sales_orders,
            "dispatches": self._export_dispatches,
        }

        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            meta = {
                "tenant_id": self.tenant.pk,
                "tenant_name": self.tenant.name,
                "tenant_slug": self.tenant.slug,
                "exported_at": exported_at,
                "entity_types": list(self.entity_types),
                "date_from": self.date_from.isoformat() if self.date_from else None,
                "date_to": self.date_to.isoformat() if self.date_to else None,
            }
            zf.writestr(f"{slug}/manifest.json", json.dumps(meta, indent=2, default=_json_serializer))

            for entity_type in self.entity_types:
                handler = handlers.get(entity_type)
                if not handler:
                    continue
                json_rows, csv_rows = handler()
                zf.writestr(
                    f"{slug}/{entity_type}.json",
                    json.dumps(json_rows, indent=2, default=_json_serializer),
                )
                csv_buf = io.StringIO()
                writer = csv.writer(csv_buf)
                for row in csv_rows:
                    writer.writerow(row)
                zf.writestr(f"{slug}/{entity_type}.csv", csv_buf.getvalue())

        buffer.seek(0)
        return buffer
