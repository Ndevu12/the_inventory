"""API views for inventory models."""

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from inventory.exceptions import InventoryError, InsufficientStockError, MovementImmutableError
from inventory.models import Category, Product, StockLocation, StockLot, StockMovement, StockRecord
from inventory.services.cache import (
    cache_get,
    cache_set,
    stock_record_serialized_cache_key,
)
from inventory.services.stock import StockService
from tenants.context import get_current_tenant
from tenants.middleware import resolve_tenant_for_request
from tenants.permissions import TenantReadOnlyOrManager, get_membership

from api.mixins import TranslatableAPIReadMixin
from api.schema_i18n import OPENAPI_LANGUAGE_QUERY_PARAMETER
from api.serializers.inventory import (
    CategorySerializer,
    ProductSerializer,
    StockLocationSerializer,
    StockLotSerializer,
    StockMovementCreateSerializer,
    StockMovementSerializer,
    StockRecordSerializer,
)
from api.views.reservation import product_availability_action


class TenantScopedInventoryMixin:
    """Tenant resolution, membership checks, and RBAC for inventory APIs.

    Replaces the global ``IsStaffUser`` default with tenant-aware
    permissions so that non-staff tenant members (managers, admins, etc.)
    can use CRUD endpoints while viewers get read-only access.

    Thread-local context may be unset when DRF authenticates after
    :class:`~tenants.middleware.TenantMiddleware` (e.g. token auth); in that
    case we resolve the tenant from the authenticated user via
    ``resolve_tenant_for_request``.
    """

    permission_classes = [IsAuthenticated, TenantReadOnlyOrManager]

    def _get_current_tenant(self):
        tenant = get_current_tenant()
        if tenant is None:
            tenant = resolve_tenant_for_request(self.request)
        if tenant is None:
            raise PermissionDenied("No tenant context available.")
        if not get_membership(self.request.user, tenant):
            raise PermissionDenied("User does not belong to this tenant.")
        return tenant

    def _verify_tenant_ownership(self, obj):
        """Ensure ``obj`` belongs to the tenant resolved for this request."""
        tenant = self._get_current_tenant()
        if obj.tenant_id != tenant.pk:
            raise PermissionDenied("Object does not belong to the current tenant.")

    def perform_create(self, serializer):
        tenant = self._get_current_tenant()
        created_by = self.request.user if self.request.user.is_authenticated else None
        try:
            serializer.save(tenant=tenant, created_by=created_by)
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A record with these unique fields already exists for this tenant."}
            ) from exc

    def perform_update(self, serializer):
        self._verify_tenant_ownership(serializer.instance)
        try:
            serializer.save()
        except IntegrityError as exc:
            raise ValidationError(
                {"detail": "A record with these unique fields already exists for this tenant."}
            ) from exc

    def perform_destroy(self, instance):
        self._verify_tenant_ownership(instance)
        instance.delete()


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class CategoryViewSet(TranslatableAPIReadMixin, TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "slug"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class ProductViewSet(TranslatableAPIReadMixin, TenantScopedInventoryMixin, viewsets.ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ["category", "unit_of_measure", "is_active"]
    search_fields = ["sku", "name"]
    ordering_fields = ["sku", "name", "unit_cost", "created_at"]
    ordering = ["sku"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def get_object(self):
        """Detail writes/retrieve use tenant-scoped queryset (404 if wrong tenant).

        Custom stock-related actions resolve PK globally then enforce membership so
        cross-tenant PKs return 403, matching :mod:`tests.api.test_inventory_tenant_security`.
        """
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg]}
        if getattr(self, "action", None) in (
            "stock", "movements", "availability", "lots",
        ):
            obj = get_object_or_404(Product.objects.all(), **filter_kwargs)
            self.check_object_permissions(self.request, obj)
            self._verify_tenant_ownership(obj)
            return obj
        obj = get_object_or_404(self.get_queryset(), **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def _product_for_stock_operations(self, product: Product) -> Product:
        """Stock/movements are keyed to the tenant canonical locale row."""
        loc = getattr(self, "_api_canonical_locale", None)
        if loc is None or product.locale_id == loc.id:
            return product
        canonical = product.get_translation_or_none(loc)
        return canonical if canonical is not None else product

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        """Return stock records for this product across all locations."""
        tenant = self._get_current_tenant()
        product = self._product_for_stock_operations(self.get_object())
        self._verify_tenant_ownership(product)
        records = StockRecord.objects.filter(
            product=product,
            tenant=tenant,
        ).select_related("location")
        ctx = self.get_serializer_context()
        lang = ctx.get("language")
        data = []
        for record in records:
            key = stock_record_serialized_cache_key(
                product.pk, record.location_id, lang,
            )
            cached = cache_get(key)
            if cached is not None:
                data.append(cached)
            else:
                serialized = StockRecordSerializer(record, context=ctx).data
                cache_set(key, serialized)
                data.append(serialized)
        return Response(data)

    @action(detail=True, methods=["get"])
    def movements(self, request, pk=None):
        """Return recent stock movements for this product."""
        tenant = self._get_current_tenant()
        product = self._product_for_stock_operations(self.get_object())
        self._verify_tenant_ownership(product)
        movements = StockMovement.objects.filter(
            product=product,
            tenant=tenant,
        ).select_related("from_location", "to_location")[:50]
        serializer = StockMovementSerializer(
            movements, many=True, context=self.get_serializer_context(),
        )
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def availability(self, request, pk=None):
        """Return per-location availability: quantity, reserved, available."""
        product = self._product_for_stock_operations(self.get_object())
        self._verify_tenant_ownership(product)
        return product_availability_action(self, request, product=product)

    @action(detail=True, methods=["get"])
    def lots(self, request, pk=None):
        """Return lots for this product, with optional filtering."""
        tenant = self._get_current_tenant()
        product = self._product_for_stock_operations(self.get_object())
        self._verify_tenant_ownership(product)
        qs = StockLot.objects.filter(product=product, tenant=tenant).select_related("product")

        is_active = request.query_params.get("is_active")
        if is_active is not None:
            qs = qs.filter(is_active=is_active.lower() in ("true", "1"))

        expiry_before = request.query_params.get("expiry_date__lte")
        if expiry_before:
            qs = qs.filter(expiry_date__lte=expiry_before)

        qs = qs.order_by("received_date")
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = StockLotSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = StockLotSerializer(qs, many=True)
        return Response(serializer.data)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class StockLocationViewSet(
    TranslatableAPIReadMixin,
    TenantScopedInventoryMixin,
    viewsets.ModelViewSet,
):
    queryset = StockLocation.objects.all()
    serializer_class = StockLocationSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    @action(detail=True, methods=["get"])
    def stock(self, request, pk=None):
        """Return stock records at this location."""
        tenant = self._get_current_tenant()
        location = get_object_or_404(StockLocation.objects.all(), pk=pk)
        self._verify_tenant_ownership(location)
        records = StockRecord.objects.filter(
            location=location,
            tenant=tenant,
        ).select_related("product")
        ctx = self.get_serializer_context()
        lang = ctx.get("language")
        data = []
        for record in records:
            key = stock_record_serialized_cache_key(
                record.product_id, location.pk, lang,
            )
            cached = cache_get(key)
            if cached is not None:
                data.append(cached)
            else:
                serialized = StockRecordSerializer(record, context=ctx).data
                cache_set(key, serialized)
                data.append(serialized)
        return Response(data)


class StockRecordViewSet(TranslatableAPIReadMixin, TenantScopedInventoryMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only — stock is managed through movements, not direct edits."""

    queryset = StockRecord.objects.select_related("product", "location").all()
    serializer_class = StockRecordSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["product", "location"]
    ordering_fields = ["quantity", "product__sku"]
    ordering = ["product__sku"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    @action(detail=False, methods=["get"])
    def low_stock(self, request):
        """Return stock records that are at or below the product's reorder point."""
        tenant = self._get_current_tenant()
        records = [r for r in self.get_queryset() if r.is_low_stock]
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)


@extend_schema(parameters=[OPENAPI_LANGUAGE_QUERY_PARAMETER])
class StockMovementViewSet(TranslatableAPIReadMixin,
                           TenantScopedInventoryMixin,
                           viewsets.GenericViewSet,
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

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)

    def get_serializer_class(self):
        if self.action == "create":
            return StockMovementCreateSerializer
        return StockMovementSerializer

    def create(self, request, *args, **kwargs):
        tenant = self._get_current_tenant()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data
        product = data["product"]
        if product.tenant_id != tenant.pk:
            raise PermissionDenied("Product does not belong to the current tenant.")
        for loc in (data.get("from_location"), data.get("to_location")):
            if loc is not None and loc.tenant_id != tenant.pk:
                raise PermissionDenied("Location does not belong to the current tenant.")

        service = StockService()
        created_by = request.user if request.user.is_authenticated else None

        try:
            if serializer.has_lot_fields:
                movement = service.process_movement_with_lots(
                    product=data["product"],
                    movement_type=data["movement_type"],
                    quantity=data["quantity"],
                    from_location=data.get("from_location"),
                    to_location=data.get("to_location"),
                    unit_cost=data.get("unit_cost"),
                    reference=data.get("reference", ""),
                    notes=data.get("notes", ""),
                    lot_number=data.get("lot_number", ""),
                    serial_number=data.get("serial_number", ""),
                    manufacturing_date=data.get("manufacturing_date"),
                    expiry_date=data.get("expiry_date"),
                    allocation_strategy=data.get("allocation_strategy", "FIFO"),
                    created_by=created_by,
                )
            else:
                movement = service.process_movement(
                    product=data["product"],
                    movement_type=data["movement_type"],
                    quantity=data["quantity"],
                    from_location=data.get("from_location"),
                    to_location=data.get("to_location"),
                    unit_cost=data.get("unit_cost"),
                    reference=data.get("reference", ""),
                    notes=data.get("notes", ""),
                    created_by=created_by,
                )
        except (InsufficientStockError, MovementImmutableError) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_409_CONFLICT,
            )
        except InventoryError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except DjangoValidationError as e:
            return Response(
                {"detail": e.message if hasattr(e, "message") else str(e)},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        output = StockMovementSerializer(
            movement, context=self.get_serializer_context(),
        )
        return Response(output.data, status=status.HTTP_201_CREATED)


class StockLotViewSet(TenantScopedInventoryMixin, viewsets.ReadOnlyModelViewSet):
    """Read-only — lots are created via stock movements, not directly."""

    queryset = (
        StockLot.objects
        .select_related("product", "supplier", "purchase_order")
        .all()
    )
    serializer_class = StockLotSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        "product": ["exact"],
        "is_active": ["exact"],
        "expiry_date": ["exact", "lte", "gte"],
        "lot_number": ["exact"],
    }
    search_fields = ["lot_number", "serial_number", "product__sku"]
    ordering_fields = ["received_date", "expiry_date", "quantity_remaining", "created_at"]
    ordering = ["-received_date"]

    def get_queryset(self):
        tenant = self._get_current_tenant()
        return super().get_queryset().filter(tenant=tenant)
