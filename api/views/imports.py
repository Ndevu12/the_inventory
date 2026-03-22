"""Data import API view — CSV/Excel file upload."""

from rest_framework import serializers, status
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from inventory.imports.importers import CustomerImporter, ProductImporter, SupplierImporter
from inventory.imports.parsers import parse_csv, parse_excel
from tenants.middleware import get_effective_tenant

DATA_TYPE_MAP = {
    "products": ProductImporter,
    "suppliers": SupplierImporter,
    "customers": CustomerImporter,
}


class ImportUploadSerializer(serializers.Serializer):
    data_type = serializers.ChoiceField(choices=list(DATA_TYPE_MAP.keys()))
    file = serializers.FileField()

    def validate_file(self, value):
        allowed = (".csv", ".xlsx")
        name = value.name.lower()
        if not any(name.endswith(ext) for ext in allowed):
            raise serializers.ValidationError(
                f"Unsupported file type. Allowed: {', '.join(allowed)}"
            )
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be under 5 MB.")
        return value


class ImportDataView(APIView):
    """Upload a CSV or Excel file to bulk-import master data.

    POST with ``multipart/form-data``:
    - ``data_type``: one of ``products``, ``suppliers``, ``customers``
    - ``file``: the CSV or XLSX file
    """

    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,)

    def post(self, request):
        ser = ImportUploadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)

        file_obj = ser.validated_data["file"]
        data_type = ser.validated_data["data_type"]

        if file_obj.name.lower().endswith(".xlsx"):
            rows = parse_excel(file_obj)
        else:
            rows = parse_csv(file_obj)

        importer_cls = DATA_TYPE_MAP[data_type]
        tenant = get_effective_tenant(request)
        importer = importer_cls(rows=rows, tenant=tenant, user=request.user)
        result = importer.run()

        if result.success:
            return Response(
                {"created": result.created_count, "errors": []},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"created": 0, "errors": result.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
