"""Wagtail admin views for CSV/Excel data import."""

from django.contrib import messages
from django.views.generic import FormView
from wagtail.admin.views.generic.base import WagtailAdminTemplateMixin

from inventory.imports.forms import ImportForm
from inventory.imports.importers import CustomerImporter, ProductImporter, SupplierImporter
from inventory.imports.parsers import parse_csv, parse_excel


IMPORTER_MAP = {
    "products": ProductImporter,
    "suppliers": SupplierImporter,
    "customers": CustomerImporter,
}

TEMPLATE_HEADERS = {
    "products": ["sku", "name", "description", "unit_of_measure", "unit_cost", "reorder_point", "is_active"],
    "suppliers": ["code", "name", "contact_name", "email", "phone", "address", "lead_time_days", "payment_terms", "notes"],
    "customers": ["code", "name", "contact_name", "email", "phone", "address", "notes"],
}


class DataImportView(WagtailAdminTemplateMixin, FormView):
    """Upload a CSV or Excel file to bulk-import master data."""

    template_name = "inventory/import.html"
    form_class = ImportForm
    page_title = "Import Data"
    header_icon = "upload"

    def form_valid(self, form):
        file_obj = form.cleaned_data["file"]
        data_type = form.cleaned_data["data_type"]

        filename = file_obj.name.lower()
        if filename.endswith((".xlsx", ".xls")):
            rows = parse_excel(file_obj)
        else:
            rows = parse_csv(file_obj)

        importer_class = IMPORTER_MAP[data_type]
        importer = importer_class(
            rows=rows,
            tenant=getattr(self.request, "tenant", None),
            user=self.request.user,
        )
        result = importer.run()

        if result.success:
            messages.success(
                self.request,
                f"Successfully imported {result.created_count} {data_type}.",
            )
        else:
            for error in result.errors:
                if error["row"]:
                    msg = f"Row {error['row']}"
                    if error["field"]:
                        msg += f", {error['field']}"
                    msg += f": {error['message']}"
                else:
                    msg = error["message"]
                messages.error(self.request, msg)

        return self.render_to_response(
            self.get_context_data(form=form, result=result),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template_headers"] = TEMPLATE_HEADERS
        context.setdefault("result", None)
        return context
