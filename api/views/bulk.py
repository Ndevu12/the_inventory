"""API views for bulk stock operations."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.bulk import (
    BulkAdjustmentSerializer,
    BulkOperationResultSerializer,
    BulkRevalueSerializer,
    BulkTransferSerializer,
)
from inventory.exceptions import InventoryError
from inventory.services.bulk import BulkStockService
from tenants.permissions import IsTenantAdmin, IsTenantManager


class BulkTransferView(APIView):
    """``POST /api/v1/bulk-operations/transfer/`` — managers+"""

    permission_classes = [IsAuthenticated, IsTenantManager]

    def post(self, request):
        serializer = BulkTransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = BulkStockService()
        created_by = request.user if request.user.is_authenticated else None

        items = [
            {"product_id": item["product_id"], "quantity": item["quantity"]}
            for item in data["items"]
        ]

        try:
            result = service.bulk_transfer(
                items=items,
                from_location=data["from_location"],
                to_location=data["to_location"],
                reference=data.get("reference", ""),
                notes=data.get("notes", ""),
                created_by=created_by,
                fail_fast=data.get("fail_fast", False),
            )
        except InventoryError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        output = BulkOperationResultSerializer(result)
        http_status = (
            status.HTTP_200_OK
            if result.failure_count == 0
            else status.HTTP_207_MULTI_STATUS
        )
        return Response(output.data, status=http_status)


class BulkAdjustmentView(APIView):
    """``POST /api/v1/bulk-operations/adjust/`` — managers+"""

    permission_classes = [IsAuthenticated, IsTenantManager]

    def post(self, request):
        serializer = BulkAdjustmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = BulkStockService()
        created_by = request.user if request.user.is_authenticated else None

        items = [
            {"product_id": item["product_id"], "new_quantity": item["new_quantity"]}
            for item in data["items"]
        ]

        try:
            result = service.bulk_adjustment(
                items=items,
                location=data["location"],
                notes=data.get("notes", ""),
                created_by=created_by,
                fail_fast=data.get("fail_fast", False),
            )
        except InventoryError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        output = BulkOperationResultSerializer(result)
        http_status = (
            status.HTTP_200_OK
            if result.failure_count == 0
            else status.HTTP_207_MULTI_STATUS
        )
        return Response(output.data, status=http_status)


class BulkRevalueView(APIView):
    """``POST /api/v1/bulk-operations/revalue/`` — admins+"""

    permission_classes = [IsAuthenticated, IsTenantAdmin]

    def post(self, request):
        serializer = BulkRevalueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        service = BulkStockService()

        items = [
            {
                "product_id": item["product_id"],
                "new_unit_cost": item["new_unit_cost"],
            }
            for item in data["items"]
        ]

        try:
            result = service.bulk_revalue(
                items=items,
                fail_fast=data.get("fail_fast", False),
            )
        except InventoryError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        output = BulkOperationResultSerializer(result)
        http_status = (
            status.HTTP_200_OK
            if result.failure_count == 0
            else status.HTTP_207_MULTI_STATUS
        )
        return Response(output.data, status=http_status)
