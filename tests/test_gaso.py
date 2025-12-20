"""
Tests for GASO (PowerBI) integration.
"""


def test_gaso_responds(gaso_responses):
    """GASO API returns something for each test DNI."""
    for dni, resp in gaso_responses.items():
        assert resp is not None, f"No response for {dni}"
        assert "status" in resp, f"Missing status for {dni}"


def test_gaso_status_valid(gaso_responses):
    """Status is always one of expected values."""
    valid = {"success", "not_found", "error", "timeout"}
    for dni, resp in gaso_responses.items():
        assert resp["status"] in valid, (
            f"Unexpected status '{resp['status']}' for {dni}"
        )


def test_gaso_success_has_segmento(gaso_responses):
    """CRITICAL: successful responses include segmento='gaso'."""
    for dni, resp in gaso_responses.items():
        if resp["status"] == "success" and resp["data"]:
            data = resp["data"]
            assert "segmento" in data, f"Missing segmento for {dni}"
            assert data["segmento"] == "gaso", (
                f"Wrong segmento for {dni}: {data['segmento']}"
            )


def test_gaso_success_has_required_fields(gaso_responses):
    """Successful responses have fields needed for Chatwoot."""
    required = ["dni", "nombre", "tieneLineaCredito", "segmento"]
    for dni, resp in gaso_responses.items():
        if resp["status"] == "success" and resp["data"]:
            for field in required:
                assert field in resp["data"], f"Missing {field} for {dni}"


def test_gaso_tiene_linea_credito_is_bool(gaso_responses):
    """tieneLineaCredito must be boolean, not string."""
    for dni, resp in gaso_responses.items():
        if resp["status"] == "success" and resp["data"]:
            val = resp["data"].get("tieneLineaCredito")
            assert isinstance(val, bool), f"tieneLineaCredito is {type(val)} for {dni}"


def test_gaso_linea_credito_is_number(gaso_responses):
    """lineaCredito must be numeric."""
    for dni, resp in gaso_responses.items():
        if resp["status"] == "success" and resp["data"]:
            val = resp["data"].get("lineaCredito")
            if val is not None:
                assert isinstance(val, (int, float)), (
                    f"lineaCredito is {type(val)} for {dni}"
                )


# def test_show_gaso_data(gaso_responses):
#     """Debug: print actual GASO data to see what formats exist."""
#     for dni, resp in gaso_responses.items():
#         print(f"\nGASO {dni}:")
#         print(f"status: {resp['status']}")
#         if resp["data"]:
#             for k, v in resp["data"].items():
#                 print(f"  {k}: {v!r} ({type(v).__name__})")
#     assert False  # fail to see output
