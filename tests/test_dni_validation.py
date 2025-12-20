import pytest
from vcc_totem.core.query import validate_dni


def test_valid_dni():
    assert validate_dni("12345678") == "12345678"


def test_strips_whitespace():
    assert validate_dni("  12345678  ") == "12345678"


def test_leading_zeros_ok():
    assert validate_dni("00123456") == "00123456"


# INVALID DNIs
def test_rejects_letters():
    with pytest.raises(ValueError):
        validate_dni("1234567A")


def test_rejects_7_digits():
    with pytest.raises(ValueError):
        validate_dni("1234567")


def test_rejects_9_digits():
    with pytest.raises(ValueError):
        validate_dni("123456789")


def test_rejects_empty():
    with pytest.raises(ValueError):
        validate_dni("")


def test_rejects_spaces_inside():
    with pytest.raises(ValueError):
        validate_dni("1234 5678")


def test_rejects_dashes():
    with pytest.raises(ValueError):
        validate_dni("12-345-678")
