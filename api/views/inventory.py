"""API views for inventory models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from inventory.models import Category, Product, StockLocation, StockMovement, StockRecord
from inventory.services.stock import StockService

from api.serializers.inventory import (
    CategorySerializer,
    ProductSerializer,
    StockLocationSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
    StockRecordSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "unit_of_measure", "is_active"]
    search_fields = ["sku", "name"]
    ordering_fields = ["sku", "name", "unit_cost", "created_at"]
    ordering = ["sku"]

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        """Return stock records for this product across all locations."""
        product = self.get_object()
        records = StockRecord.objects.filter(
            product=product,
        ).select_related("location")
        serializer = StockRecordSerializer(records, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        """Return recent stock movements for this product."""
        product = self.get_object()
        movements = StockMovement.objects.filter(
            product=product,
        ).select_related("from_location", "to_location")[:50]
        serializer = StockMovementSerializer(movements, many=True)
        return Response(serializer.data)


class StockLocationViewSet(viewsets.ModelViewSet):
    queryset = StockLocation.objects.all()
    serializer_class = StockLocationSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        """Return stock records at this location."""
        location = self.get_object()
        records = StockRecord.objects.filter(
            location=location,
        ).select_related("product")
        serializer = StockRecordSerializer(records, many=True)
        return Response(serializer.data)


class StockRecordViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only — stock is managed through movements, not direct edits."""

    queryset = StockRecord.objects.select_related("product", "location").all()
    serializer_class = StockRecordSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["product", "location"]
    ordering_fields = ["quantity", "product__sku"]
    ordering = ["product__sku"]

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Return stock records that are at or below the product's reorder point."""
        records = [r for r in self.get_queryset() if r.is_low_stock]
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)


class StockMovementViewSet(viewsets.GenericViewSet,
                           viewsets.mixins.ListModelMixin,
                           viewsets.mixins.RetrieveModelMixin,
                           viewsets.mixins.CreateModelMixin):
    """List/retrieve/create stock movements.

    Create goes through ``StockService.process_movement()`` to ensure
    atomic stock updates.  Movements cannot be updated or deleted.
    """

    queryset = StockMovement.objects.select_related(
        "product", "from_location", "to_location", "created_by",
    ).all()
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["product", "movement_type", "from_location", "to_location"]
    ordering_fields = ["created_at", "quantity"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "create":
            return StockMovementCreateSerializer
        return StockMovementSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        service = StockService()
        try:
            movement = service.process_movement(
                product=serializer.validated_data["product"],
                movement_type=serializer.validated_data["movement_type"],
                quantity=serializer.validated_data["quantity"],
                from_location=serializer.validated_data.get("from_location"),
                to_location=serializer.validated_data.get("to_location"),
                unit_cost=serializer.validated_data.get("unit_cost"),
                reference=serializer.validated_data.get("reference", ""),
                notes=serializer.validated_data.get("notes", ""),
                created_by=request.user if request.user.is_authenticated else None,
            )
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        output = StockMovementSerializer(movement)
        return Response(output.data, status=status.HTTP_201_CREATED)
