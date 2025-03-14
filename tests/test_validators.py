import pytest
from playdo.validators import validate_password_complexity


@pytest.mark.parametrize(
    "password, expected_result",
    [
        # Valid passwords (at least 12 chars with letters and numbers)
        ("SecurePass123", True),
        ("LongPassword1234567890", True),
        ("abc123def456ghi", True),
        ("12345abcdef67890", True),
        ("a1b2c3d4e5f6g7", True),
        # Invalid passwords - too short
        ("", False),
        ("short123", False),
        ("abc123", False),
        # Invalid passwords - missing letters
        ("12345678901234", False),
        ("0123456789012", False),
        # Invalid passwords - missing numbers
        ("abcdefghijklmnop", False),
        ("SecurePasswordNoNumbers", False),
        # Edge cases
        ("           1a", True),  # Mostly spaces but meets requirements
        ("12345abcdefg", True),  # Exactly 12 characters
        ("A" + "1" * 11, True),  # One letter, 11 numbers
        ("1" + "A" * 11, True),  # One number, 11 letters
    ],
)
def test_validate_password_complexity(password, expected_result):
    """Test the password complexity validation with various inputs."""
    assert validate_password_complexity(password) == expected_result
