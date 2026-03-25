"""API views for stock reservations and product availability."""

from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from api.filters.cycle_reservation import StockReservationFilter
from api.mixins import TranslatableAPIReadMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.reservation import (
    StockReservationCreateSerializer,
    StockReservationSerializer,
)
from inventory.exceptions import (
    InsufficientStockError,
    InventoryError,
    ReservationConflictError,
)
from inventory.models import StockRecord, StockReservation
from inventory.models.reservation import ReservationStatus
from inventory.services.reservation import ReservationService
from inventory.utils.localized_attributes import attribute_in_display_locale
from tenants.context import get_current_tenant
from tenants.middleware import resolve_tenant_for_request
from tenants.permissions import TenantReadOnlyOrManager, get_membership

_ACTIVE_STATUSES = [ReservationStatus.PENDING, ReservationStatus.CONFIRMED]


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class StockReservationViewSet(TranslatableAPIReadMixin,
                              viewsets.GenericViewSet,
                              viewsets.mixins.ListModelMixin,
                              viewsets.mixins.RetrieveModelMixin,
                              viewsets.mixins.CreateModelMixin):
    """Manage stock reservations.

    Owners, admins, and managers can create, fulfill, and cancel reservations.
    All tenant members can list and retrieve.
    """

    queryset = (
        StockReservation.objects
        .select_related(
            "product", "location", "location__warehouse",
            "sales_order", "reserved_by",
        )
        .all()
    )
    permission_classes = [IsAuthenticated, TenantReadOnlyOrManager]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = StockReservationFilter
    ordering_fields = ["created_at", "expires_at", "quantity"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return StockReservationCreateSerializer
        return StockReservationSerializer

    def _get_current_tenant(self):
        tenant = get_current_tenant()
        if tenant is None:
            tenant = resolve_tenant_for_request(self.request)
        if tenant is None:
            raise PermissionDenied("No tenant context available.")
        if not get_membership(self.request.user, tenant):
            raise PermissionDenied("User does not belong to this tenant.")
        return tenant

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        service = ReservationService()
        reserved_by = request.user if request.user.is_authenticated else None

        try:
            reservation = service.create_reservation(
                product=data["product"],
                location=data["location"],
                quantity=data["quantity"],
                sales_order=data.get("sales_order"),
                reserved_by=reserved_by,
                notes=data.get("notes", ""),
            )
        except InsufficientStockError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except (ValueError, InventoryError) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        output = StockReservationSerializer(
            reservation, context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        """Fulfill a reservation by issuing stock."""
        reservation = self.get_object()
        service = ReservationService()
        created_by = request.user if request.user.is_authenticated else None

        try:
            service.fulfill_reservation(reservation, created_by=created_by)
        except ReservationConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except InsufficientStockError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        reservation.refresh_from_db()
        output = StockReservationSerializer(
            reservation, context=self.get_serializer_context(),
        )
        return Response(output.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        """Cancel a pending or confirmed reservation."""
        reservation = self.get_object()
        service = ReservationService()

        try:
            service.cancel_reservation(reservation)
        except ReservationConflictError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )

        reservation.refresh_from_db()
        output = StockReservationSerializer(
            reservation, context=self.get_serializer_context(),
        )
        return Response(output.data)


def product_availability_action(self, request, pk=None, product=None):
    """Return per-location availability for a product.

    Aggregates stock quantity, active reservations, and available qty.
    When ``product`` is omitted, resolves it via ``get_object()`` (tenant-scoped).
    """
    tenant = self._get_current_tenant()
    if product is None:
        product = self.get_object()
    records = (
        StockRecord.objects
        .filter(product=product, tenant=tenant)
        .select_related("location")
    )

    display_loc = getattr(self, "_api_display_locale", None)
    result = []
    for record in records:
        reserved = (
            StockReservation.objects
            .filter(
                product=product,
                location=record.location,
                status__in=_ACTIVE_STATUSES,
                tenant=tenant,
            )
            .aggregate(total=Sum("quantity"))
        )["total"] or 0

        result.append({
            "location": record.location.pk,
            "location_name": attribute_in_display_locale(
                record.location, "name", display_loc,
            ),
            "quantity": record.quantity,
            "reserved": reserved,
            "available": max(record.quantity - reserved, 0),
        })

    return Response(result)
