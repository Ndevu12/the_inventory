"""API views for cycle count management."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from api.permissions import ReadOnlyOrStaff
from api.serializers.cycle import (
    CycleCreateSerializer,
    InventoryCycleDetailSerializer,
    InventoryCycleSerializer,
    ReconcileSerializer,
    RecordCountSerializer,
)
from inventory.models.cycle import InventoryCycle
from inventory.services.cycle import CycleCountService

import logging

logger = logging.getLogger(__name__)


class InventoryCycleViewSet(viewsets.GenericViewSet,
                            viewsets.mixins.ListModelMixin,
                            viewsets.mixins.RetrieveModelMixin):
    """Manage inventory cycle counts.

    Supports listing, retrieving, starting (creating), recording counts,
    completing, and reconciling cycles.
    """

    queryset = (
        InventoryCycle.objects
        .select_related("location", "started_by")
        .prefetch_related("lines", "variances")
        .all()
    )
    permission_classes = [ReadOnlyOrStaff]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]
    filterset_fields = ["status", "location"]
    search_fields = ["name"]
    ordering_fields = ["scheduled_date", "created_at", "started_at", "completed_at"]
    ordering = ["-scheduled_date"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return InventoryCycleDetailSerializer
        return InventoryCycleSerializer

    @action(detail=False, methods=["post"])
    def start(self, request):
        """Start a new cycle count. Creates the cycle and pre-populates count lines."""
        serializer = CycleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = CycleCountService()

        try:
            cycle = service.start_cycle(
                name=data["name"],
                location=data.get("location"),
                scheduled_date=data["scheduled_date"],
                started_by=request.user,
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        if data.get("notes"):
            cycle.notes = data["notes"]
            cycle.save(update_fields=["notes"])

        output = InventoryCycleDetailSerializer(cycle)
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="record-count")
    def record_count(self, request, pk=None):
        """Record a physical count for one product at one location in this cycle."""
        cycle = self.get_object()
        serializer = RecordCountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = CycleCountService()

        try:
            service.record_count(
                cycle,
                product=data["product"],
                location=data["location"],
                counted_quantity=data["counted_quantity"],
                counted_by=request.user,
                notes=data.get("notes", ""),
            )
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        cycle.refresh_from_db()
        output = InventoryCycleDetailSerializer(cycle)
        return Response(output.data)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark cycle as completed. No more counts accepted afterward."""
        cycle = self.get_object()
        service = CycleCountService()

        try:
            service.complete_cycle(cycle)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)

        cycle.refresh_from_db()
        output = InventoryCycleDetailSerializer(cycle)
        return Response(output.data)

    @action(detail=True, methods=["post"])
    def reconcile(self, request, pk=None):
        """Reconcile all variances: accept, investigate, or reject each line."""
        cycle = self.get_object()
        serializer = ReconcileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = CycleCountService()

        try:
            service.reconcile_cycle(
                cycle,
                resolved_by=request.user,
                resolutions=data["resolutions"],
            )
        except ValueError as e:
            logger.warning("Failed to reconcile inventory cycle %s: %s", cycle.id, e, exc_info=True)
            return Response(
                {"detail": "Unable to reconcile this cycle."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        cycle.refresh_from_db()
        output = InventoryCycleDetailSerializer(cycle)
        return Response(output.data)
