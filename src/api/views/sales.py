"""API views for sales models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Prefetch
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from api.serializers.localized_strings import attribute_in_display_locale
from inventory.audit_crud import log_tenant_audit
from inventory.models import AuditAction
from sales.models import Customer, Dispatch, SalesOrder
from sales.services.sales import SalesService

from api.mixins import TranslatableAPIReadMixin
from api.mixins.audited_crud import AuditedTenantCRUDMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.sales import (
    CustomerSerializer,
    DispatchSerializer,
    SalesOrderSerializer,
)
from api.views.inventory import TenantScopedInventoryMixin


def _django_validation_detail(exc: DjangoValidationError) -> str:
    """Single string for DRF ``{"detail": ...}`` from a Django validation error."""
    message_dict = getattr(exc, "message_dict", None)
    if message_dict:
        for val in message_dict.values():
            if isinstance(val, list) and val:
                return str(val[0])
            if val:
                return str(val)
    messages = getattr(exc, "messages", None)
    if messages:
        return str(messages[0])
    # Fall back to a generic message instead of exposing the raw exception.
    return "Invalid data."


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class CustomerViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "contact_name"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    audit_action_create = AuditAction.CUSTOMER_CREATED
    audit_action_update = AuditAction.CUSTOMER_UPDATED
    audit_action_delete = AuditAction.CUSTOMER_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "customer",
            "object_id": instance.pk,
            "code": instance.code,
            "name": instance.name,
        }


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class SalesOrderViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = SalesOrder.objects.select_related("customer").prefetch_related(
        "lines",
        "lines__product",
        Prefetch(
            "dispatches",
            queryset=Dispatch.objects.select_related(
                "from_location", "from_location__warehouse",
            ).order_by("-dispatch_date", "-pk"),
        ),
    ).all()
    serializer_class = SalesOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "customer"]
    search_fields = ["order_number", "customer__name"]
    ordering_fields = ["order_date", "order_number", "created_at"]
    ordering = ["-order_date"]

    audit_action_create = AuditAction.SALES_ORDER_CREATED
    audit_action_update = AuditAction.SALES_ORDER_UPDATED
    audit_action_delete = AuditAction.SALES_ORDER_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "salesorder",
            "object_id": instance.pk,
            "order_number": instance.order_number,
            "status": instance.status,
        }

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a draft sales order."""
        so = self.get_object()
        service = SalesService()
        try:
            service.confirm_order(
                sales_order=so,
                confirmed_by=request.user,
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": _django_validation_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        so.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.SALES_ORDER_CONFIRMED,
            object_type="salesorder",
            object_id=so.pk,
            order_number=so.order_number,
            status=so.status,
        )
        return Response(self.get_serializer(so).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a sales order."""
        so = self.get_object()
        service = SalesService()
        try:
            service.cancel_order(sales_order=so)
        except DjangoValidationError as exc:
            return Response(
                {"detail": _django_validation_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        so.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.SALES_ORDER_CANCELLED,
            object_type="salesorder",
            object_id=so.pk,
            order_number=so.order_number,
            status=so.status,
        )
        return Response(self.get_serializer(so).data)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class DispatchViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = Dispatch.objects.select_related(
        "sales_order", "from_location", "from_location__warehouse",
    ).all()
    serializer_class = DispatchSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_processed", "sales_order"]
    ordering_fields = ["dispatch_date", "created_at"]
    ordering = ["-dispatch_date"]

    audit_action_create = AuditAction.DISPATCH_CREATED
    audit_action_update = AuditAction.DISPATCH_UPDATED
    audit_action_delete = AuditAction.DISPATCH_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "dispatch",
            "object_id": instance.pk,
            "dispatch_number": instance.dispatch_number,
            "sales_order_id": instance.sales_order_id,
        }

    @extend_schema(
        parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "issue_available_only": {"type": "boolean"},
                },
            },
        },
    )
    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Process this dispatch — create issue stock movements."""
        dispatch = self.get_object()
        service = SalesService()
        issue_available_only = bool(
            (request.data or {}).get("issue_available_only"),
        )
        try:
            service.process_dispatch(
                dispatch=dispatch,
                dispatched_by=request.user,
                issue_available_only=issue_available_only,
            )
        except DjangoValidationError as exc:
            return Response(
                {"detail": _django_validation_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dispatch.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.DISPATCH_PROCESSED,
            object_type="dispatch",
            object_id=dispatch.pk,
            dispatch_number=dispatch.dispatch_number,
            sales_order_id=dispatch.sales_order_id,
        )
        return Response(self.get_serializer(dispatch).data)

    @extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
    @action(detail=True, methods=["get"], url_path="fulfillment-preview")
    def fulfillment_preview(self, request, pk=None):
        """Ordered vs available (unreserved) quantities at the dispatch source."""
        dispatch = self.get_object()
        service = SalesService()
        try:
            payload = service.fulfillment_preview(dispatch=dispatch)
        except DjangoValidationError as exc:
            return Response(
                {"detail": _django_validation_detail(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        display_locale = getattr(self, "_api_display_locale", None)
        line_map = {
            ln.id: ln
            for ln in dispatch.sales_order.lines.select_related("product").order_by(
                "pk",
            )
        }
        for row in payload["lines"]:
            line = line_map.get(row["line_id"])
            product = line.product if line else None
            row["product_name"] = attribute_in_display_locale(
                product, "name", display_locale,
            )
        return Response(payload)
