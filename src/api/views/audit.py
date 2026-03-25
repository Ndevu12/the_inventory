"""Audit log API — tenant and platform audit with CSV/Excel export."""

import csv
from io import BytesIO

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from drf_spectacular.utils import extend_schema
from openpyxl import Workbook
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated

from api.mixins import TranslatableAPIReadMixin
from api.pagination import StandardPagination
from api.permissions import IsPlatformSuperuser, IsTenantMemberAuthorizedForAuditLog
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.audit import (
    ComplianceAuditLogSerializer,
    PlatformAuditLogSerializer,
)
from inventory.models import AuditAction, ComplianceAuditLog
from inventory.utils.localized_attributes import attribute_in_display_locale
from tenants.middleware import get_effective_tenant
from tenants.permissions import get_membership

_TENANT_CSV_HEADERS = [
    "ID", "Timestamp", "Action", "Product SKU", "Product",
    "User", "IP Address", "Details",
]

_PLATFORM_CSV_HEADERS = [
    "ID", "Timestamp", "Tenant", "Action", "Object Type", "Object ID",
    "Product SKU", "Product", "User", "IP Address", "Details",
]


class AuditLogFilter(FilterSet):
    date_from = filters.DateTimeFilter(field_name="timestamp", lookup_expr="gte")
    date_to = filters.DateTimeFilter(field_name="timestamp", lookup_expr="lte")
    action = filters.ChoiceFilter(choices=AuditAction.choices)
    product = filters.NumberFilter(field_name="product_id")
    user = filters.NumberFilter(field_name="user_id")

    class Meta:
        model = ComplianceAuditLog
        fields = ["date_from", "date_to", "action", "product", "user"]


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class ComplianceAuditLogViewSet(TranslatableAPIReadMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only audit log with filtering and CSV export.

    Accessible only to organization governance roles (owner/coordinator), JWT-safe via
    :class:`~api.permissions.IsTenantMemberAuthorizedForAuditLog`.

    Filters
    -------
    - ``date_from`` / ``date_to`` — timestamp range
    - ``action`` — one of :class:`~inventory.models.audit.AuditAction`
    - ``product`` — product id
    - ``user`` — user id

    CSV export
    ----------
    Append ``?export=csv`` to any list request to download the filtered
    result set as a CSV file.
    """

    queryset = (
        ComplianceAuditLog.objects
        .select_related("product", "user")
        .all()
    )
    serializer_class = ComplianceAuditLogSerializer
    permission_classes = [IsAuthenticated, IsTenantMemberAuthorizedForAuditLog]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AuditLogFilter
    ordering = ["-timestamp"]

    def _get_current_tenant(self):
        tenant = get_effective_tenant(self.request)
        if tenant is None:
            raise PermissionDenied("No tenant context set.")
        if not get_membership(self.request.user, tenant=tenant):
            raise PermissionDenied("User does not belong to this tenant.")
        return tenant

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_effective_tenant(self.request)
        if tenant is None:
            return qs.none()
        return qs.filter(tenant=tenant)

    def list(self, request, *args, **kwargs):
        if request.query_params.get("export") == "csv":
            return self._export_csv(request)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """Dedicated ``/export/`` endpoint that always returns CSV."""
        return self._export_csv(request)

    def _export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_log.csv"'

        writer = csv.writer(response)
        writer.writerow(_TENANT_CSV_HEADERS)
        loc = getattr(self, "_api_display_locale", None)
        for entry in qs.iterator():
            prod_name = ""
            if entry.product_id:
                prod_name = attribute_in_display_locale(entry.product, "name", loc) or ""
            writer.writerow([
                entry.pk,
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else "",
                entry.get_action_display(),
                getattr(entry.product, "sku", "") if entry.product_id else "",
                prod_name,
                getattr(entry.user, "username", ""),
                entry.ip_address or "",
                str(entry.details) if entry.details else "",
            ])
        return response


class PlatformAuditLogFilter(AuditLogFilter):
    """Platform audit filter with tenant filter."""

    tenant = filters.NumberFilter(field_name="tenant_id")

    class Meta(AuditLogFilter.Meta):
        fields = AuditLogFilter.Meta.fields + ["tenant"]


def _platform_export_row(entry, display_locale=None):
    """Build a row for CSV/Excel export (platform view)."""
    obj_type = "product" if entry.product_id else "general"
    obj_id = str(entry.product_id) if entry.product_id else ""
    if not obj_id and entry.details and isinstance(entry.details, dict):
        for key in ("object_id", "cycle_id", "reservation_id", "lot_id"):
            if entry.details.get(key) is not None:
                obj_id = str(entry.details[key])
                break
    tenant_name = entry.tenant.name if entry.tenant_id else ""
    prod_name = ""
    if entry.product_id:
        prod_name = attribute_in_display_locale(entry.product, "name", display_locale) or ""
    return [
        entry.pk,
        entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else "",
        tenant_name,
        entry.get_action_display(),
        obj_type,
        obj_id,
        getattr(entry.product, "sku", "") if entry.product_id else "",
        prod_name,
        getattr(entry.user, "username", ""),
        entry.ip_address or "",
        str(entry.details) if entry.details else "",
    ]


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class PlatformAuditLogViewSet(TranslatableAPIReadMixin, viewsets.ReadOnlyModelViewSet):
    """Platform-wide audit log for superusers.

    List all audit entries across tenants with filters and export.

    Filters
    -------
    - ``tenant`` — tenant id
    - ``date_from`` / ``date_to`` — timestamp range
    - ``action`` — one of :class:`~inventory.models.audit.AuditAction`
    - ``product`` — product id
    - ``user`` — user id

    Export
    ------
    - ``?format=csv`` or ``?export=csv`` — CSV download
    - ``?format=xlsx`` or ``?export=xlsx`` — Excel download
    """

    queryset = (
        ComplianceAuditLog.objects
        .select_related("product", "user", "tenant")
        .all()
    )
    serializer_class = PlatformAuditLogSerializer
    permission_classes = [IsAuthenticated, IsPlatformSuperuser]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PlatformAuditLogFilter
    ordering = ["-timestamp"]

    def _get_current_tenant(self):
        return get_effective_tenant(self.request)

    def list(self, request, *args, **kwargs):
        fmt = request.query_params.get("format") or request.query_params.get("export")
        if fmt == "csv":
            return self._export_csv(request)
        if fmt == "xlsx":
            return self._export_xlsx(request)
        return super().list(request, *args, **kwargs)

    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request):
        """Export endpoint: ?format=csv or ?format=xlsx."""
        fmt = request.query_params.get("format", "csv")
        if fmt == "xlsx":
            return self._export_xlsx(request)
        return self._export_csv(request)

    def _export_csv(self, request):
        qs = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="platform_audit_log.csv"'

        writer = csv.writer(response)
        writer.writerow(_PLATFORM_CSV_HEADERS)
        loc = getattr(self, "_api_display_locale", None)
        for entry in qs.iterator():
            writer.writerow(_platform_export_row(entry, display_locale=loc))
        return response

    def _export_xlsx(self, request):
        qs = self.filter_queryset(self.get_queryset())
        wb = Workbook()
        ws = wb.active
        ws.title = "Audit Log"
        ws.append(_PLATFORM_CSV_HEADERS)
        loc = getattr(self, "_api_display_locale", None)
        for entry in qs.iterator():
            ws.append(_platform_export_row(entry, display_locale=loc))

        buf = BytesIO()
        wb.save(buf)
        buf.seek(0)

        response = HttpResponse(
            buf.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = (
            'attachment; filename="platform_audit_log.xlsx"'
        )
        return response
