import re
from django.core.exceptions import ValidationError


PHONE_NUMBER_REGEX = re.compile(r"^\+?[0-9\s\-()]{7,20}$")


def validate_phone_number(value):
    """
    Validate phone numbers with patterns that include optional country code, spaces,hyphens, and parentheses.
    """
    if value in (None, ""):
        return

    if not PHONE_NUMBER_REGEX.fullmatch(value):
        raise ValidationError(
            "Enter a valid phone number."
        )
