"""Audit log API — list and CSV export for compliance audit entries."""

import csv

from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from api.permissions import IsAdminOrOwner
from api.serializers.audit import ComplianceAuditLogSerializer
from inventory.models import AuditAction, ComplianceAuditLog

_CSV_HEADERS = [
    "ID", "Timestamp", "Action", "Product SKU", "Product",
    "User", "IP Address", "Details",
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


class ComplianceAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only audit log with filtering and CSV export.

    Accessible only to tenant admins and owners.

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
    permission_classes = [IsAuthenticated, IsAdminOrOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AuditLogFilter
    ordering = ["-timestamp"]

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
        writer.writerow(_CSV_HEADERS)
        for entry in qs.iterator():
            writer.writerow([
                entry.pk,
                entry.timestamp.strftime("%Y-%m-%d %H:%M:%S") if entry.timestamp else "",
                entry.get_action_display(),
                getattr(entry.product, "sku", ""),
                getattr(entry.product, "name", ""),
                getattr(entry.user, "username", ""),
                entry.ip_address or "",
                str(entry.details) if entry.details else "",
            ])
        return response
