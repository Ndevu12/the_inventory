"""API views for sales models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from api.serializers.localized_strings import (
    attribute_in_display_locale,
    display_locale_from_context,
)
from sales.models import Customer, Dispatch, SalesOrder
from sales.services.sales import SalesService

from api.mixins import TranslatableAPIReadMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.sales import (
    CustomerSerializer,
    DispatchSerializer,
    SalesOrderSerializer,
)
from api.views.inventory import TenantScopedInventoryMixin


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class CustomerViewSet(TranslatableAPIReadMixin, TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active"]
    search_fields = ["code", "name", "contact_name"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class SalesOrderViewSet(
    TranslatableAPIReadMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = SalesOrder.objects.select_related("customer").prefetch_related(
        "lines", "lines__product",
    ).all()
    serializer_class = SalesOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "customer"]
    search_fields = ["order_number", "customer__name"]
    ordering_fields = ["order_date", "order_number", "created_at"]
    ordering = ["-order_date"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

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
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(so).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a sales order."""
        so = self.get_object()
        service = SalesService()
        try:
            service.cancel_order(sales_order=so)
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(so).data)


class DispatchViewSet(TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = Dispatch.objects.select_related(
        "sales_order", "from_location",
    ).all()
    serializer_class = DispatchSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_processed", "sales_order"]
    ordering_fields = ["dispatch_date", "created_at"]
    ordering = ["-dispatch_date"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

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
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dispatch.refresh_from_db()
        return Response(self.get_serializer(dispatch).data)

    @extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
    @action(detail=True, methods=["get"], url_path="fulfillment-preview")
    def fulfillment_preview(self, request, pk=None):
        """Ordered vs available (unreserved) quantities at the dispatch source."""
        dispatch = self.get_object()
        service = SalesService()
        try:
            payload = service.fulfillment_preview(dispatch=dispatch)
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        display_locale = display_locale_from_context({"request": request})
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
