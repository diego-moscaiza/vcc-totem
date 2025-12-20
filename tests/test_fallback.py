"""
Tests for the fallback mechanism.

FNB first, then GASO if not found.
"""

from vcc_totem.models import QueryResult
from vcc_totem.core.query import query_with_fallback, query_fnb, query_gaso


def test_query_result_found_client():
    """found_client is True when success + data."""
    r = QueryResult(success=True, dni="123", channel="fnb", data={"x": 1})
    assert r.found_client is True


def test_query_result_not_found():
    """found_client is False when no data."""
    r = QueryResult(success=True, dni="123", channel="fnb", data=None)
    assert r.found_client is False


def test_query_result_failed():
    """found_client is False when failed."""
    r = QueryResult(success=False, dni="123", channel="fnb", error_message="err")
    assert r.found_client is False


def test_query_fnb_returns_result(test_dnis):
    """query_fnb returns QueryResult."""
    result = query_fnb(test_dnis[0])

    assert isinstance(result, QueryResult)
    assert result.channel == "fnb"


def test_query_gaso_returns_result(test_dnis):
    """query_gaso returns QueryResult."""
    result = query_gaso(test_dnis[0])

    assert isinstance(result, QueryResult)
    assert result.channel == "gaso"


def test_fallback_returns_result(test_dnis):
    """query_with_fallback returns QueryResult."""
    result = query_with_fallback(test_dnis[0])

    assert isinstance(result, QueryResult)
    assert result.channel in ["fnb", "gaso"]


def test_fallback_invalid_dni_no_crash():
    """Fallback handles invalid DNI gracefully."""
    result = query_with_fallback("00000000")

    assert isinstance(result, QueryResult)
    # Should not crash, just return failure
