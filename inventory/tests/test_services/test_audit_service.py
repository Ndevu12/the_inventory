"""Unit and integration tests for AuditService.

Unit tests exercise ``AuditService.log()`` and
``AuditService.log_from_request()`` in isolation.  The integration test
at the bottom verifies that processing a stock movement via
:class:`StockService` produces both a ``StockMovement`` *and* a
``ComplianceAuditLog`` entry.
"""

from decimal import Decimal
from types import SimpleNamespace

from django.test import TestCase

from inventory.models import MovementType
from inventory.models.audit import AuditAction, ComplianceAuditLog
from inventory.services.audit import AuditService
from inventory.services.stock import StockService

from ..factories import (
    create_location,
    create_product,
    create_tenant,
    create_user,
)


# =====================================================================
# Unit tests — AuditService.log()
# =====================================================================


class AuditServiceLogTests(TestCase):
    """Test ``AuditService.log()`` in isolation."""

    def setUp(self):
        self.service = AuditService()
        self.tenant = create_tenant()
        self.user = create_user(username="auditor")
        self.product = create_product(sku="AUD-001", tenant=self.tenant)

    def test_creates_audit_log_entry(self):
        entry = self.service.log(
            tenant=self.tenant,
            action=AuditAction.STOCK_RECEIVED,
            user=self.user,
            product=self.product,
        )
        self.assertIsNotNone(entry.pk)
        self.assertEqual(entry.tenant, self.tenant)
        self.assertEqual(entry.action, AuditAction.STOCK_RECEIVED)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.product, self.product)

    def test_stores_extra_details_as_json(self):
        entry = self.service.log(
            tenant=self.tenant,
            action=AuditAction.STOCK_ISSUED,
            user=self.user,
            quantity=42,
            location="Warehouse A",
        )
        self.assertEqual(entry.details["quantity"], 42)
        self.assertEqual(entry.details["location"], "Warehouse A")

    def test_ip_address_stored(self):
        entry = self.service.log(
            tenant=self.tenant,
            action=AuditAction.STOCK_RECEIVED,
            ip_address="192.168.1.100",
        )
        self.assertEqual(entry.ip_address, "192.168.1.100")

    def test_user_and_product_optional(self):
        entry = self.service.log(
            tenant=self.tenant,
            action=AuditAction.TENANT_ACCESSED,
        )
        self.assertIsNone(entry.user)
        self.assertIsNone(entry.product)

    def test_empty_details_stored_as_empty_dict(self):
        entry = self.service.log(
            tenant=self.tenant,
            action=AuditAction.STOCK_RECEIVED,
        )
        self.assertEqual(entry.details, {})

    def test_log_persists_to_database(self):
        self.service.log(
            tenant=self.tenant,
            action=AuditAction.STOCK_RECEIVED,
            user=self.user,
        )
        self.assertEqual(ComplianceAuditLog.objects.count(), 1)
        stored = ComplianceAuditLog.objects.first()
        self.assertEqual(stored.action, AuditAction.STOCK_RECEIVED)
        self.assertEqual(stored.user, self.user)


# =====================================================================
# Unit tests — AuditService.log_from_request()
# =====================================================================


class AuditServiceLogFromRequestTests(TestCase):
    """Test ``AuditService.log_from_request()`` with mock requests."""

    def setUp(self):
        self.service = AuditService()
        self.tenant = create_tenant(slug="req-tenant")
        self.user = create_user(username="requser")
        self.product = create_product(sku="REQ-001", tenant=self.tenant)

    def _make_request(self, *, tenant=None, user=None, meta=None):
        """Build a lightweight request-like object."""
        request = SimpleNamespace()
        request.tenant = tenant
        request.user = user
        request.META = meta or {}
        return request

    def test_extracts_tenant_and_user(self):
        request = self._make_request(
            tenant=self.tenant,
            user=self.user,
            meta={"REMOTE_ADDR": "10.0.0.1"},
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.STOCK_RECEIVED,
            product=self.product,
        )
        self.assertEqual(entry.tenant, self.tenant)
        self.assertEqual(entry.user, self.user)
        self.assertEqual(entry.product, self.product)

    def test_ip_from_remote_addr(self):
        request = self._make_request(
            tenant=self.tenant,
            meta={"REMOTE_ADDR": "10.0.0.1"},
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.STOCK_RECEIVED,
        )
        self.assertEqual(entry.ip_address, "10.0.0.1")

    def test_ip_from_x_forwarded_for(self):
        request = self._make_request(
            tenant=self.tenant,
            meta={
                "HTTP_X_FORWARDED_FOR": "203.0.113.50, 70.41.3.18, 150.172.238.178",
                "REMOTE_ADDR": "127.0.0.1",
            },
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.STOCK_RECEIVED,
        )
        self.assertEqual(entry.ip_address, "203.0.113.50")

    def test_x_forwarded_for_takes_precedence(self):
        request = self._make_request(
            tenant=self.tenant,
            meta={
                "HTTP_X_FORWARDED_FOR": "1.2.3.4",
                "REMOTE_ADDR": "5.6.7.8",
            },
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.STOCK_RECEIVED,
        )
        self.assertEqual(entry.ip_address, "1.2.3.4")

    def test_anonymous_user_stored_as_none(self):
        anon = SimpleNamespace(is_authenticated=False)
        request = self._make_request(
            tenant=self.tenant,
            user=anon,
            meta={"REMOTE_ADDR": "10.0.0.1"},
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.TENANT_ACCESSED,
        )
        self.assertIsNone(entry.user)

    def test_passes_extra_details(self):
        request = self._make_request(
            tenant=self.tenant,
            user=self.user,
            meta={"REMOTE_ADDR": "10.0.0.1"},
        )
        entry = self.service.log_from_request(
            request,
            action=AuditAction.BULK_OPERATION,
            batch_size=500,
            operation="import",
        )
        self.assertEqual(entry.details["batch_size"], 500)
        self.assertEqual(entry.details["operation"], "import")

    def test_missing_tenant_on_request(self):
        """When request has no tenant attr, None is passed to log()."""
        request = SimpleNamespace(
            user=self.user,
            META={"REMOTE_ADDR": "10.0.0.1"},
        )
        # ComplianceAuditLog.tenant is required (non-nullable FK),
        # so this should raise an IntegrityError.
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            self.service.log_from_request(
                request,
                action=AuditAction.STOCK_RECEIVED,
            )


# =====================================================================
# Integration test — StockMovement + ComplianceAuditLog
# =====================================================================


class StockMovementAuditIntegrationTests(TestCase):
    """Verify that processing a stock movement creates both records."""

    def setUp(self):
        self.tenant = create_tenant(slug="integ-tenant")
        self.user = create_user(username="warehouse-op")
        self.product = create_product(
            sku="INT-001",
            tenant=self.tenant,
            unit_cost=Decimal("9.99"),
        )
        self.warehouse = create_location(name="Integration Warehouse")
        self.store = create_location(name="Integration Store")
        self.service = StockService()

    def test_receive_creates_audit_log(self):
        movement = self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            unit_cost=Decimal("9.99"),
            created_by=self.user,
        )

        logs = ComplianceAuditLog.objects.filter(tenant=self.tenant)
        self.assertEqual(logs.count(), 1)

        log = logs.first()
        self.assertEqual(log.action, AuditAction.STOCK_RECEIVED)
        self.assertEqual(log.product, self.product)
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.details["movement_id"], movement.pk)
        self.assertEqual(log.details["quantity"], 100)
        self.assertEqual(log.details["to_location"], "Integration Warehouse")
        self.assertEqual(log.details["unit_cost"], "9.99")

    def test_issue_creates_audit_log(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            created_by=self.user,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
            created_by=self.user,
        )

        issue_log = ComplianceAuditLog.objects.filter(
            action=AuditAction.STOCK_ISSUED,
        ).first()
        self.assertIsNotNone(issue_log)
        self.assertEqual(issue_log.details["quantity"], 20)
        self.assertEqual(issue_log.details["from_location"], "Integration Warehouse")

    def test_transfer_creates_audit_log(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            created_by=self.user,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
            created_by=self.user,
        )

        transfer_log = ComplianceAuditLog.objects.filter(
            action=AuditAction.STOCK_TRANSFERRED,
        ).first()
        self.assertIsNotNone(transfer_log)
        self.assertEqual(transfer_log.details["quantity"], 30)
        self.assertEqual(transfer_log.details["from_location"], "Integration Warehouse")
        self.assertEqual(transfer_log.details["to_location"], "Integration Store")

    def test_adjustment_creates_audit_log(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ADJUSTMENT,
            quantity=15,
            to_location=self.warehouse,
            created_by=self.user,
        )

        log = ComplianceAuditLog.objects.filter(
            action=AuditAction.STOCK_ADJUSTED,
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.details["quantity"], 15)

    def test_no_audit_log_without_tenant(self):
        """Products without a tenant skip audit logging gracefully."""
        product_no_tenant = create_product(sku="NO-TENANT-001", tenant=None)
        self.service.process_movement(
            product=product_no_tenant,
            movement_type=MovementType.RECEIVE,
            quantity=10,
            to_location=self.warehouse,
        )
        self.assertEqual(ComplianceAuditLog.objects.count(), 0)

    def test_movement_sequence_creates_multiple_logs(self):
        """Each movement in a sequence gets its own audit log entry."""
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=100,
            to_location=self.warehouse,
            created_by=self.user,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.ISSUE,
            quantity=20,
            from_location=self.warehouse,
            created_by=self.user,
        )
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.TRANSFER,
            quantity=30,
            from_location=self.warehouse,
            to_location=self.store,
            created_by=self.user,
        )

        self.assertEqual(ComplianceAuditLog.objects.filter(tenant=self.tenant).count(), 3)

    def test_reference_included_in_audit_details(self):
        self.service.process_movement(
            product=self.product,
            movement_type=MovementType.RECEIVE,
            quantity=50,
            to_location=self.warehouse,
            reference="PO-2026-001",
            created_by=self.user,
        )
        log = ComplianceAuditLog.objects.first()
        self.assertEqual(log.details["reference"], "PO-2026-001")
