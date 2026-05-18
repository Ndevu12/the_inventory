from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from src.api.validators import validate_phone_number


class PhoneNumberValidatorTests(SimpleTestCase):
    def test_valid_phone_numbers(self):
        valid_numbers = [
            "9876543210",
            "+919876543210",
            "+91 98765 43210",
            "98765-43210",
        ]

        for phone in valid_numbers:
            with self.subTest(phone=phone):
                validate_phone_number(phone)

    def test_invalid_phone_numbers(self):
        invalid_numbers = [
            "abc123",
            "123",
            "phone-number",
            "!!!!",
        ]

        for phone in invalid_numbers:
            with self.subTest(phone=phone):
                with self.assertRaises(ValidationError):
                    validate_phone_number(phone)