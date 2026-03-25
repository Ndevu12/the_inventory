"""API views for procurement models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from inventory.audit_crud import log_tenant_audit
from inventory.models import AuditAction
from procurement.models import GoodsReceivedNote, PurchaseOrder, Supplier
from procurement.services.procurement import ProcurementService

from api.mixins import TranslatableAPIReadMixin
from api.mixins.audited_crud import AuditedTenantCRUDMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.procurement import (
    GoodsReceivedNoteSerializer,
    PurchaseOrderSerializer,
    SupplierSerializer,
)
from api.views.inventory import TenantScopedInventoryMixin

import logging

logger = logging.getLogger(__name__)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class SupplierViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["is_active", "payment_terms"]
    search_fields = ["code", "name", "contact_name"]
    ordering_fields = ["name", "code", "created_at"]
    ordering = ["name"]

    audit_action_create = AuditAction.SUPPLIER_CREATED
    audit_action_update = AuditAction.SUPPLIER_UPDATED
    audit_action_delete = AuditAction.SUPPLIER_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "supplier",
            "object_id": instance.pk,
            "code": instance.code,
            "name": instance.name,
        }


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class PurchaseOrderViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
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

    audit_action_create = AuditAction.PURCHASE_ORDER_CREATED
    audit_action_update = AuditAction.PURCHASE_ORDER_UPDATED
    audit_action_delete = AuditAction.PURCHASE_ORDER_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "purchaseorder",
            "object_id": instance.pk,
            "order_number": instance.order_number,
            "status": instance.status,
        }

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
        except DjangoValidationError:
            logger.exception("Validation error while confirming purchase order %s", po.pk)
            return Response(
                {"detail": "Could not confirm this purchase order due to validation errors."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.PURCHASE_ORDER_CONFIRMED,
            object_type="purchaseorder",
            object_id=po.pk,
            order_number=po.order_number,
            status=po.status,
        )
        return Response(self.get_serializer(po).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a purchase order."""
        po = self.get_object()
        service = ProcurementService()
        try:
            service.cancel_order(purchase_order=po)
        except DjangoValidationError:
            logger.exception("Validation error while cancelling purchase order %s", po.pk)
            return Response(
                {"detail": "Could not cancel this purchase order due to validation errors."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        po.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.PURCHASE_ORDER_CANCELLED,
            object_type="purchaseorder",
            object_id=po.pk,
            order_number=po.order_number,
            status=po.status,
        )
        return Response(self.get_serializer(po).data)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class GoodsReceivedNoteViewSet(
    TranslatableAPIReadMixin,
    AuditedTenantCRUDMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = GoodsReceivedNote.objects.select_related(
        "purchase_order", "location", "location__warehouse",
    ).all()
    serializer_class = GoodsReceivedNoteSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["is_processed", "purchase_order"]
    ordering_fields = ["received_date", "created_at"]
    ordering = ["-received_date"]

    audit_action_create = AuditAction.GRN_CREATED
    audit_action_update = AuditAction.GRN_UPDATED
    audit_action_delete = AuditAction.GRN_DELETED

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def _audit_log_payload(self, instance):
        return None, {
            "object_type": "goodsreceivednote",
            "object_id": instance.pk,
            "grn_number": instance.grn_number,
            "purchase_order_id": instance.purchase_order_id,
        }

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
        except DjangoValidationError:
            logger.exception("Validation error while receiving goods for GRN %s", grn.pk)
            return Response(
                {"detail": "Could not process this goods received note due to validation errors."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        grn.refresh_from_db()
        log_tenant_audit(
            request,
            self._get_current_tenant(),
            AuditAction.GRN_RECEIVED,
            object_type="goodsreceivednote",
            object_id=grn.pk,
            grn_number=grn.grn_number,
            purchase_order_id=grn.purchase_order_id,
        )
        return Response(self.get_serializer(grn).data)
