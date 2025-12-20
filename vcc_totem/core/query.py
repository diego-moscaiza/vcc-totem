import logging

from vcc_totem.models import QueryResult
from vcc_totem.clients import fnb, gaso, session

logger = logging.getLogger(__name__)


def query_with_fallback(dni: str) -> QueryResult:
    result_fnb = query_fnb(dni)

    if result_fnb.found_client:
        return result_fnb

    return query_gaso(dni)


def query_fnb(dni: str) -> QueryResult:
    try:
        sess, ally_id = session.get_session()
        data, status, error = fnb.query_credit_line(sess, dni, ally_id)

        if status == "success" and data:
            return QueryResult(
                success=True,
                dni=dni,
                channel="fnb",
                data=data,
                has_offer=data.get("tieneLineaCredito", False),
            )

        if status == "not_found":
            return QueryResult(
                success=False,
                dni=dni,
                channel="fnb",
                error_message=error or "Client not found",
            )

        if status == "session_expired":
            logger.warning(f"Session expired for DNI {dni}, retrying")
            session.invalidate_session()
            sess, ally_id = session.get_session()
            data, status, error = fnb.query_credit_line(sess, dni, ally_id)

            if status == "success" and data:
                return QueryResult(
                    success=True,
                    dni=dni,
                    channel="fnb",
                    data=data,
                    has_offer=data.get("tieneLineaCredito", False),
                )

        return QueryResult(
            success=False,
            dni=dni,
            channel="fnb",
            error_message=error or f"Query failed: {status}",
        )

    except Exception as e:
        logger.error(f"FNB query failed for DNI {dni}: {e}")
        return QueryResult(success=False, dni=dni, channel="fnb", error_message=str(e))


def query_gaso(dni: str) -> QueryResult:
    try:
        data, status, error = gaso.query_credit_line(dni)

        if status == "success" and data:
            return QueryResult(
                success=True,
                dni=dni,
                channel="gaso",
                data=data,
                has_offer=data.get("tieneLineaCredito", False),
            )

        return QueryResult(
            success=False,
            dni=dni,
            channel="gaso",
            error_message=error or "Client not found",
        )

    except Exception as e:
        logger.error(f"GASO query failed for DNI {dni}: {e}")
        return QueryResult(success=False, dni=dni, channel="gaso", error_message=str(e))


def validate_dni(dni: str) -> str:
    dni = dni.strip()

    if not dni.isdigit():
        raise ValueError("DNI must contain only digits")

    if len(dni) != 8:
        raise ValueError("DNI must be exactly 8 digits")

    return dni
