from django import forms


class ImportForm(forms.Form):
    DATA_TYPE_CHOICES = [
        ("products", "Products"),
        ("suppliers", "Suppliers"),
        ("customers", "Customers"),
    ]

    data_type = forms.ChoiceField(
        choices=DATA_TYPE_CHOICES,
        help_text="Select the type of data to import.",
    )
    file = forms.FileField(
        help_text="Upload a CSV or Excel (.xlsx) file.",
    )

    def clean_file(self):
        f = self.cleaned_data["file"]
        name = f.name.lower()
        if not name.endswith((".csv", ".xlsx", ".xls")):
            raise forms.ValidationError(
                "Unsupported file format. Please upload a .csv or .xlsx file."
            )
        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError("File size must not exceed 10 MB.")
        return f
