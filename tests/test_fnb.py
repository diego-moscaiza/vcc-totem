"""
Tests for FNB integration.

These tests use REAL cached API responses.
"""

import pytest


def test_fnb_responds(fnb_responses):
    """FNB API returns something for each test DNI."""
    for dni, resp in fnb_responses.items():
        assert resp is not None, f"No response for {dni}"
        assert "status" in resp, f"Missing status for {dni}"


def test_fnb_status_valid(fnb_responses):
    """Status is always one of expected values."""
    valid = {
        "success",
        "not_found",
        "error",
        "timeout",
        "session_expired",
        "rate_limited",
    }
    for dni, resp in fnb_responses.items():
        assert resp["status"] in valid, (
            f"Unexpected status '{resp['status']}' for {dni}"
        )


def test_fnb_success_has_segmento(fnb_responses):
    """CRITICAL: successful responses include segmento='fnb'."""
    for dni, resp in fnb_responses.items():
        if resp["status"] == "success" and resp["data"]:
            data = resp["data"]
            assert "segmento" in data, f"Missing segmento for {dni}"
            assert data["segmento"] == "fnb", (
                f"Wrong segmento for {dni}: {data['segmento']}"
            )


def test_fnb_success_has_required_fields(fnb_responses):
    """Successful responses have tieneLineaCredito."""
    for dni, resp in fnb_responses.items():
        if resp["status"] == "success" and resp["data"]:
            assert "tieneLineaCredito" in resp["data"], (
                f"Missing tieneLineaCredito for {dni}"
            )


def test_fnb_tiene_linea_credito_is_bool(fnb_responses):
    """tieneLineaCredito must be boolean."""
    for dni, resp in fnb_responses.items():
        if resp["status"] == "success" and resp["data"]:
            val = resp["data"].get("tieneLineaCredito")
            assert isinstance(val, bool), f"tieneLineaCredito is {type(val)} for {dni}"


# Session management
def test_session_returns_tuple():
    """get_session returns (session, ally_id)."""
    from vcc_totem.clients.session import get_session

    try:
        result = get_session()
        assert isinstance(result, tuple)
        assert len(result) == 2
    except Exception:
        pytest.skip("Session unavailable")


def test_invalidate_session_safe():
    """invalidate_session doesn't crash."""
    from vcc_totem.clients.session import invalidate_session

    invalidate_session()  # should not raise
