"""
Validation should primarily be done at the model level, but this module is for validation
that cannot be done at the model level, because (for instance) the fields are not directly
stored on the model (a password hash, rather than a password, is stored).
"""

import re


def validate_password_complexity(password: str) -> bool:
    """
    Validate password complexity requirements.
    Password must be at least 12 characters and contain both letters and numbers.
    """
    if not password:
        return False
    if len(password) < 12:
        return False
    if not re.search(r"[A-Za-z]", password) or not re.search(r"[0-9]", password):
        return False
    return True
