"""Data importers for bulk-creating master data from parsed rows.

Each importer validates rows, collects errors, and performs a bulk
create within a transaction.  The import is all-or-nothing: if any
row fails validation, no records are created.

Usage::

    importer = ProductImporter(rows=parsed_rows, tenant=tenant, user=request.user)
    result = importer.run()
    # result.success → bool
    # result.created_count → int
    # result.errors → list[dict]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from django.db import transaction

from tenants.context import get_current_tenant

_UNSET_LOCALE = object()


@dataclass
class ImportResult:
    success: bool = False
    created_count: int = 0
    errors: list[dict] = field(default_factory=list)

    def add_error(self, row_num: int, field_name: str, message: str):
        self.errors.append({
            "row": row_num,
            "field": field_name,
            "message": message,
        })


class BaseImporter:
    """Base class for all data importers.

    Subclasses must define ``REQUIRED_COLUMNS``, ``MODEL``, and
    implement ``validate_row()`` and ``build_instance()``.
    """

    REQUIRED_COLUMNS: tuple[str, ...] = ()
    MODEL = None
    #: Set True for :class:`~wagtail.models.TranslatableMixin` catalog rows.
    REQUIRES_WAGTAIL_LOCALE = False

    def __init__(self, *, rows: list[dict], tenant=None, user=None):
        self.rows = rows
        self.tenant = tenant or get_current_tenant()
        self.user = user
        self.result = ImportResult()
        self._default_wagtail_locale_cache = _UNSET_LOCALE

    def get_default_wagtail_locale(self):
        """Wagtail locale for tenant canonical language, else first configured locale."""
        if self._default_wagtail_locale_cache is not _UNSET_LOCALE:
            return self._default_wagtail_locale_cache
        from wagtail.models import Locale

        from api.language import resolve_canonical_language_code, wagtail_locale_for_language

        code = resolve_canonical_language_code(self.tenant)
        loc = wagtail_locale_for_language(code)
        if loc is None:
            loc = Locale.objects.order_by("pk").first()
        self._default_wagtail_locale_cache = loc
        return loc

    def run(self) -> ImportResult:
        if not self.rows:
            self.result.add_error(0, "", "No data rows found in file.")
            return self.result

        self._validate_columns()
        if self.result.errors:
            return self.result

        if self.REQUIRES_WAGTAIL_LOCALE and self.get_default_wagtail_locale() is None:
            self.result.add_error(
                0,
                "",
                "No Wagtail locale configured. Add at least one locale in Wagtail admin.",
            )
            return self.result

        instances = []
        for i, row in enumerate(self.rows, start=2):
            instance = self._process_row(i, row)
            if instance:
                instances.append(instance)

        if self.result.errors:
            return self.result

        with transaction.atomic():
            self.MODEL.objects.bulk_create(instances)
            self.result.created_count = len(instances)
            self.result.success = True

        return self.result

    def _validate_columns(self):
        if not self.rows:
            return
        actual = set(self.rows[0].keys())
        missing = set(self.REQUIRED_COLUMNS) - actual
        if missing:
            self.result.add_error(
                1, "", f"Missing required columns: {', '.join(sorted(missing))}"
            )

    def _process_row(self, row_num: int, row: dict):
        self.validate_row(row_num, row)
        if self.result.errors and self.result.errors[-1]["row"] == row_num:
            return None
        return self.build_instance(row)

    def validate_row(self, row_num: int, row: dict):
        raise NotImplementedError

    def build_instance(self, row: dict):
        raise NotImplementedError

    def _require(self, row_num: int, row: dict, field_name: str):
        val = row.get(field_name, "").strip()
        if not val:
            self.result.add_error(row_num, field_name, f"'{field_name}' is required.")
        return val


class ProductImporter(BaseImporter):
    """Import products from CSV/Excel.

    Required columns: ``sku``, ``name``

    Optional columns: ``unit_of_measure``, ``unit_cost``,
    ``reorder_point``, ``description``, ``is_active``
    """

    REQUIRED_COLUMNS = ("sku", "name")
    REQUIRES_WAGTAIL_LOCALE = True

    @property
    def MODEL(self):
        from inventory.models import Product
        return Product

    def validate_row(self, row_num, row):
        self._require(row_num, row, "sku")
        self._require(row_num, row, "name")

        cost = row.get("unit_cost", "").strip()
        if cost:
            try:
                Decimal(cost)
            except InvalidOperation:
                self.result.add_error(row_num, "unit_cost", f"Invalid decimal: '{cost}'")

        rp = row.get("reorder_point", "").strip()
        if rp:
            try:
                int(rp)
            except ValueError:
                self.result.add_error(row_num, "reorder_point", f"Invalid integer: '{rp}'")

    def build_instance(self, row):
        from inventory.models import Product, UnitOfMeasure

        uom = row.get("unit_of_measure", "").strip().lower()
        valid_uoms = {c.value for c in UnitOfMeasure}
        if uom not in valid_uoms:
            uom = UnitOfMeasure.PIECES

        return Product(
            sku=row["sku"].strip(),
            name=row["name"].strip(),
            description=row.get("description", "").strip(),
            unit_of_measure=uom,
            unit_cost=Decimal(row["unit_cost"].strip()) if row.get("unit_cost", "").strip() else Decimal("0"),
            reorder_point=int(row["reorder_point"].strip()) if row.get("reorder_point", "").strip() else 0,
            is_active=row.get("is_active", "true").strip().lower() not in ("false", "0", "no"),
            tenant=self.tenant,
            locale=self.get_default_wagtail_locale(),
            created_by=self.user,
        )


class SupplierImporter(BaseImporter):
    """Import suppliers from CSV/Excel.

    Required columns: ``code``, ``name``

    Optional columns: ``contact_name``, ``email``, ``phone``,
    ``address``, ``lead_time_days``, ``payment_terms``, ``notes``
    """

    REQUIRED_COLUMNS = ("code", "name")
    REQUIRES_WAGTAIL_LOCALE = True

    @property
    def MODEL(self):
        from procurement.models import Supplier
        return Supplier

    def validate_row(self, row_num, row):
        self._require(row_num, row, "code")
        self._require(row_num, row, "name")

        ltd = row.get("lead_time_days", "").strip()
        if ltd:
            try:
                int(ltd)
            except ValueError:
                self.result.add_error(row_num, "lead_time_days", f"Invalid integer: '{ltd}'")

    def build_instance(self, row):
        from procurement.models import PaymentTerms, Supplier

        pt = row.get("payment_terms", "").strip().lower()
        valid_terms = {c.value for c in PaymentTerms}
        if pt not in valid_terms:
            pt = PaymentTerms.NET_30

        return Supplier(
            code=row["code"].strip(),
            name=row["name"].strip(),
            locale=self.get_default_wagtail_locale(),
            contact_name=row.get("contact_name", "").strip(),
            email=row.get("email", "").strip(),
            phone=row.get("phone", "").strip(),
            address=row.get("address", "").strip(),
            lead_time_days=int(row["lead_time_days"].strip()) if row.get("lead_time_days", "").strip() else 0,
            payment_terms=pt,
            notes=row.get("notes", "").strip(),
            tenant=self.tenant,
            created_by=self.user,
        )


class CustomerImporter(BaseImporter):
    """Import customers from CSV/Excel.

    Required columns: ``code``, ``name``

    Optional columns: ``contact_name``, ``email``, ``phone``,
    ``address``, ``notes``
    """

    REQUIRED_COLUMNS = ("code", "name")
    REQUIRES_WAGTAIL_LOCALE = True

    @property
    def MODEL(self):
        from sales.models import Customer
        return Customer

    def validate_row(self, row_num, row):
        self._require(row_num, row, "code")
        self._require(row_num, row, "name")

    def build_instance(self, row):
        from sales.models import Customer

        return Customer(
            code=row["code"].strip(),
            name=row["name"].strip(),
            locale=self.get_default_wagtail_locale(),
            contact_name=row.get("contact_name", "").strip(),
            email=row.get("email", "").strip(),
            phone=row.get("phone", "").strip(),
            address=row.get("address", "").strip(),
            notes=row.get("notes", "").strip(),
            tenant=self.tenant,
            created_by=self.user,
        )
