"""API views for procurement models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from procurement.models import GoodsReceivedNote, PurchaseOrder, Supplier
from procurement.services.procurement import ProcurementService

from api.mixins import TranslatableAPIReadMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.procurement import (
    GoodsReceivedNoteSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)
from api.views.inventory import TenantScopedInventoryMixin


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class SupplierViewSet(TranslatableAPIReadMixin, TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "payment_terms"]
    search_fields = ["code", "name", "contact_name"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class PurchaseOrderViewSet(
    TranslatableAPIReadMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = PurchaseOrder.objects.select_related("supplier").prefetch_related(
        "lines", "lines__product",
    ).all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["status", "supplier"]
    search_fields = ["order_number", "supplier__name"]
    ordering_fields = ["order_date", "order_number", "created_at"]
    ordering = ["-order_date"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        """Confirm a draft purchase order."""
        po = self.get_object()
        service = ProcurementService()
        try:
            service.confirm_order(
                purchase_order=po,
                confirmed_by=request.user,
            )
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(po).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a purchase order."""
        po = self.get_object()
        service = ProcurementService()
        try:
            service.cancel_order(purchase_order=po)
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(self.get_serializer(po).data)


class GoodsReceivedNoteViewSet(TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = GoodsReceivedNote.objects.select_related(
        "purchase_order", "location",
    ).all()
    serializer_class = GoodsReceivedNoteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_processed", "purchase_order"]
    ordering_fields = ["received_date", "created_at"]
    ordering = ["-received_date"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        """Process this GRN — create receive stock movements."""
        grn = self.get_object()
        service = ProcurementService()
        try:
            service.receive_goods(
                goods_received_note=grn,
                received_by=request.user,
            )
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        grn.refresh_from_db()
        return Response(self.get_serializer(grn).data)
