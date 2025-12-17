"""
Tests message content for Chatwoot integration.
"""

from vcc_totem.models import QueryResult
from vcc_totem.core.messages import format_response, PHONE_NUMBER


def test_offer_has_celebration():
    """Credit offer message has celebration emoji."""
    result = QueryResult(
        success=True,
        dni="12345678",
        channel="fnb",
        data={"nombre": "JUAN", "lineaCredito": 5000},
        has_offer=True,
    )
    msg, has_offer = format_response(result)

    assert "🎉" in msg
    assert has_offer is True


def test_offer_shows_name():
    """Credit offer shows client name."""
    result = QueryResult(
        success=True,
        dni="12345678",
        channel="fnb",
        data={"nombre": "MARIA GARCIA", "lineaCredito": 1000},
        has_offer=True,
    )
    msg, _ = format_response(result)

    assert "MARIA GARCIA" in msg


def test_offer_shows_amount():
    """Credit offer shows formatted amount."""
    result = QueryResult(
        success=True,
        dni="12345678",
        channel="fnb",
        data={"nombre": "TEST", "lineaCredito": 5000},
        has_offer=True,
    )
    msg, _ = format_response(result)

    assert "5,000" in msg or "5000" in msg
    assert "S/" in msg


def test_no_credit_shows_phone():
    """No-credit message includes support phone."""
    result = QueryResult(
        success=True,
        dni="12345678",
        channel="fnb",
        data={"nombre": "TEST", "tieneLineaCredito": False},
        has_offer=False,
    )
    msg, has_offer = format_response(result)

    assert PHONE_NUMBER in msg
    assert has_offer is False


def test_no_credit_uses_info_emoji():
    """No-credit message uses info emoji, not error."""
    result = QueryResult(
        success=True,
        dni="12345678",
        channel="fnb",
        data={"nombre": "TEST"},
        has_offer=False,
    )
    msg, _ = format_response(result)

    assert "ℹ️" in msg


def test_error_uses_warning_emoji():
    result = QueryResult(
        success=False,
        dni="12345678",
        channel="fnb",
        error_message="Connection failed",
    )
    msg, has_offer = format_response(result)

    assert "⚠️" in msg
    assert has_offer is False


def test_error_hides_technical_details():
    """Error message doesn't leak internal details."""
    result = QueryResult(
        success=False,
        dni="12345678",
        channel="fnb",
        error_message="HTTP 500: Internal Server Error at /api/credit",
    )
    msg, _ = format_response(result)

    # Should not show technical stuff to user
    assert "HTTP" not in msg
    assert "500" not in msg
    assert "/api" not in msg
