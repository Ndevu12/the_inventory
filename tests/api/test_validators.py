import pytest
from django.core.exceptions import ValidationError

from api.validators import validate_phone_number


@pytest.mark.parametrize("phone", [
    "9876543210",
    "+919876543210",
    "+91 98765 43210",
    "98765-43210",
])

def test_valid_phone_numbers(phone):
    validate_phone_number(phone)


@pytest.mark.parametrize("phone", [
    "abc123",
    "123",
    "phone-number",
    "!!!!",
])

def test_invalid_phone_numbers(phone):
    with pytest.raises(ValidationError):
        validate_phone_number(phone)
