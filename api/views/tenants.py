"""Tenant management API views."""

from rest_framework import status
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.tenants import TenantMemberSerializer, TenantSerializer
from tenants.models import TenantMembership
from tenants.permissions import IsTenantAdmin, IsTenantMember


class CurrentTenantView(APIView):
    """GET / PATCH the current tenant.

    All authenticated members can read; only admins/owners can update.
    """

    def get_permissions(self):
        if self.request.method in ("GET", "HEAD", "OPTIONS"):
            return [IsAuthenticated(), IsTenantMember()]
        return [IsAuthenticated(), IsTenantAdmin()]

    def get(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."}, status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

    def patch(self, request):
        tenant = getattr(request, "tenant", None)
        if not tenant:
            return Response(
                {"detail": "No active tenant."}, status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TenantSerializer(tenant, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class TenantMemberListView(ListAPIView):
    """List all members of the current tenant."""

    serializer_class = TenantMemberSerializer
    permission_classes = (IsAuthenticated, IsTenantMember)

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return TenantMembership.objects.none()
        return (
            TenantMembership.objects.filter(tenant=tenant)
            .select_related("user")
            .order_by("-is_default", "user__username")
        )


class TenantMemberDetailView(RetrieveUpdateDestroyAPIView):
    """View / update role / remove a tenant member.

    Only admins and owners can modify or remove members.
    """

    serializer_class = TenantMemberSerializer
    permission_classes = (IsAuthenticated, IsTenantAdmin)

    def get_queryset(self):
        tenant = getattr(self.request, "tenant", None)
        if not tenant:
            return TenantMembership.objects.none()
        return TenantMembership.objects.filter(tenant=tenant).select_related("user")
