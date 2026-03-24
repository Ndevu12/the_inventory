"""Platform billing API views (SA-06).

List tenants with usage vs limits, change plan/status, suspend/reactivate.
Only platform superusers can access. No tenant context required.
"""

from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from api.permissions import IsPlatformSuperuser
from api.serializers.tenants import (
    PlatformBillingTenantSerializer,
    PlatformBillingTenantUpdateSerializer,
)
from inventory.models.audit import AuditAction
from inventory.services.audit import AuditService
from tenants.models import Tenant


class PlatformBillingTenantListView(ListAPIView):
    """List all tenants with billing/usage data (superuser only)."""

    serializer_class = PlatformBillingTenantSerializer
    permission_classes = (IsAuthenticated, IsPlatformSuperuser)
    queryset = Tenant.objects.all().order_by("name")
    pagination_class = None


class PlatformBillingTenantDetailView(RetrieveUpdateAPIView):
    """Retrieve or update a tenant's billing/subscription (superuser only)."""

    permission_classes = (IsAuthenticated, IsPlatformSuperuser)
    queryset = Tenant.objects.all()
    http_method_names = ["get", "head", "options", "patch"]

    def get_serializer_class(self):
        if self.request.method == "PATCH":
            return PlatformBillingTenantUpdateSerializer
        return PlatformBillingTenantSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = self.get_object()
        serializer = PlatformBillingTenantUpdateSerializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        output = PlatformBillingTenantSerializer(instance)
        return Response(output.data)


class PlatformBillingTenantSuspendView(APIView):
    """Suspend a tenant (set is_active=False). Ties into SA-02 deactivation."""

    permission_classes = (IsAuthenticated, IsPlatformSuperuser)

    def post(self, request, pk=None):
        tenant = Tenant.objects.filter(pk=pk).first()
        if not tenant:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not tenant.is_active:
            return Response(
                {"detail": "Tenant is already suspended."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.is_active = False
        tenant.save(update_fields=["is_active"])

        AuditService().log(
            tenant=tenant,
            action=AuditAction.TENANT_DEACTIVATED,
            user=request.user,
            ip_address=AuditService._get_client_ip(request),
            details={"reason": "Platform admin suspension (billing)"},
        )

        serializer = PlatformBillingTenantSerializer(tenant)
        return Response(serializer.data)


class PlatformBillingTenantReactivateView(APIView):
    """Reactivate a suspended tenant (set is_active=True)."""

    permission_classes = (IsAuthenticated, IsPlatformSuperuser)

    def post(self, request, pk=None):
        tenant = Tenant.objects.filter(pk=pk).first() if pk is not None else None
        if not tenant:
            return Response(
                {"detail": "Tenant not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if tenant.is_active:
            return Response(
                {"detail": "Tenant is already active."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        tenant.is_active = True
        tenant.save(update_fields=["is_active"])

        AuditService().log(
            tenant=tenant,
            action=AuditAction.TENANT_REACTIVATED,
            user=request.user,
            ip_address=AuditService._get_client_ip(request),
            details={"reason": "Platform admin reactivation (billing)"},
        )

        serializer = PlatformBillingTenantSerializer(tenant)
        return Response(serializer.data)
