"""API views for sales models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from sales.models import Customer, Dispatch, SalesOrder
from sales.services.sales import SalesService

from api.serializers.sales import (
    CustomerSerializer,
    DispatchSerializer,
    SalesOrderSerializer,
)
from api.views.inventory import TenantScopedInventoryMixin


class CustomerViewSet(TenantScopedInventoryMixin, viewsets.ModelViewSet):
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


class SalesOrderViewSet(TenantScopedInventoryMixin, viewsets.ModelViewSet):
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
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid data for confirming sales order."},
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
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid data for cancelling sales order."},
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

    @action(detail=True, methods=["post"])
    def process(self, request, pk=None):
        """Process this dispatch — create issue stock movements."""
        dispatch = self.get_object()
        service = SalesService()
        try:
            service.process_dispatch(
                dispatch=dispatch,
                dispatched_by=request.user,
            )
        except DjangoValidationError:
            return Response(
                {"detail": "Invalid data for processing dispatch."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dispatch.refresh_from_db()
        return Response(self.get_serializer(dispatch).data)
