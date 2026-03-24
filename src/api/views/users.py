"""Platform user management API views.

Operates on all users across tenants. Only superusers can access.
No tenant context is required.
"""

from django.contrib.auth import get_user_model
from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend, FilterSet, filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response

from api.pagination import StandardPagination
from api.permissions import IsPlatformSuperuser
from api.serializers.users import (
    PlatformUserCreateSerializer,
    PlatformUserDetailSerializer,
    PlatformUserListSerializer,
    PlatformUserResetPasswordSerializer,
    PlatformUserUpdateSerializer,
    TenantMembershipAssignSerializer,
)
from rest_framework.generics import ListAPIView

from api.serializers.tenants import TenantSerializer
from tenants.models import Tenant, TenantMembership, TenantRole

User = get_user_model()


class PlatformTenantListView(ListAPIView):
    """List all tenants (superuser only). Used for user creation form tenant assignment."""

    serializer_class = TenantSerializer
    permission_classes = (IsPlatformSuperuser,)
    queryset = Tenant.objects.filter(is_active=True).order_by("name")
    pagination_class = None


class PlatformUserFilter(FilterSet):
    """Filter platform users by tenant membership."""

    tenant = filters.NumberFilter(method="filter_by_tenant")

    class Meta:
        model = User
        fields = ["is_active", "is_staff", "tenant"]

    def filter_by_tenant(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(
            tenant_memberships__tenant_id=value,
            tenant_memberships__is_active=True,
        ).distinct()


class PlatformUserViewSet(viewsets.ModelViewSet):
    """CRUD for platform users (superuser only).

    GET    /platform/users/          — list all users (paginated, search, filters)
    POST   /platform/users/          — create user with optional tenant assignment
    GET    /platform/users/<id>/     — retrieve user
    PATCH  /platform/users/<id>/     — update user
    DELETE /platform/users/<id>/     — soft-delete (is_active=False)
    POST   /platform/users/<id>/reset-password/  — set new password
    POST   /platform/users/<id>/assign-tenant/    — add user to tenant
    DELETE /platform/users/<id>/memberships/<membership_id>/  — remove from tenant
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = (IsPlatformSuperuser,)
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = PlatformUserFilter
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["username", "email", "date_joined", "last_login"]
    ordering = ["-date_joined"]

    def get_serializer_class(self):
        if self.action == "list":
            return PlatformUserListSerializer
        if self.action in ("retrieve", "create"):
            return PlatformUserDetailSerializer
        return PlatformUserDetailSerializer

    def perform_destroy(self, instance):
        """Soft-delete: set is_active=False to preserve for audit."""
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    def create(self, request, *args, **kwargs):
        serializer = PlatformUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        with transaction.atomic():
            user = User.objects.create_user(
                username=data["username"],
                email=data["email"],
                password=data["password"],
                first_name=data.get("first_name", ""),
                last_name=data.get("last_name", ""),
                is_active=data.get("is_active", True),
                is_staff=True,
            )

            tenant_ids = data.get("tenant_ids", [])
            default_role = data.get("default_role", TenantRole.VIEWER)
            for i, tenant_id in enumerate(tenant_ids):
                TenantMembership.objects.get_or_create(
                    tenant_id=tenant_id,
                    user=user,
                    defaults={
                        "role": default_role,
                        "is_active": True,
                        "is_default": i == 0 and len(tenant_ids) == 1,
                    },
                )

        output = PlatformUserDetailSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = PlatformUserUpdateSerializer(
            data=request.data,
            partial=kwargs.pop("partial", True),
            context={"user": instance},
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        for field in ("email", "first_name", "last_name", "is_active", "is_staff"):
            if field in data:
                setattr(instance, field, data[field])
        instance.save()

        output = PlatformUserDetailSerializer(instance)
        return Response(output.data)

    @action(detail=True, methods=["post"])
    def reset_password(self, request, pk=None):
        """Set a new password for the user (platform admin)."""
        user = self.get_object()
        serializer = PlatformUserResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"detail": "Password has been reset."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="assign-tenant")
    def assign_tenant(self, request, pk=None):
        """Add user to a tenant."""
        user = self.get_object()
        serializer = TenantMembershipAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        membership, created = TenantMembership.objects.update_or_create(
            tenant_id=data["tenant_id"],
            user=user,
            defaults={
                "role": data.get("role", TenantRole.VIEWER),
                "is_active": True,
                "is_default": data.get("is_default", False),
            },
        )

        if created and data.get("is_default"):
            TenantMembership.objects.filter(user=user).exclude(pk=membership.pk).update(
                is_default=False
            )

        output = PlatformUserDetailSerializer(user)
        return Response(output.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["delete"],
        url_path="memberships/(?P<membership_id>[^/.]+)",
    )
    def remove_membership(self, request, pk=None, membership_id=None):
        """Remove user from a tenant (deactivate membership for audit)."""
        user = self.get_object()
        try:
            membership = TenantMembership.objects.get(
                pk=membership_id, user=user,
            )
        except TenantMembership.DoesNotExist:
            return Response(
                {"detail": "Membership not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        membership.is_active = False
        membership.save(update_fields=["is_active"])
        output = PlatformUserDetailSerializer(user)
        return Response(output.data)
