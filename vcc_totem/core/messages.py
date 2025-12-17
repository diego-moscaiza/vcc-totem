from textwrap import dedent

from vcc_totem.models import QueryResult

PHONE_NUMBER = "01-614-9000 opc 3"
DEFAULT_NAME = "Cliente"


def format_response(result: QueryResult) -> tuple[str, bool]:
    if result.success and result.has_offer:
        return _format_offer_message(result.data), True

    if result.success and not result.has_offer:
        return _format_no_credit_message(result.data), False

    if result.error_message and "not found" in result.error_message.lower():
        return _format_no_credit_message(), False

    return _format_error_message(), False


def _format_offer_message(data: dict) -> str:
    name = data.get("nombre", DEFAULT_NAME)
    amount = data.get("lineaCredito", 0)

    return dedent(f"""\
        🎉 ¡FELICITACIONES!

        Hola *{name}*,
        ¡Tenemos excelentes noticias para ti!

        ¡Tienes una línea de crédito APROBADA por:
        💰 S/ {amount:,.2f}!
    """).strip()


def _format_no_credit_message(data: dict | None = None) -> str:
    name = data.get("nombre", DEFAULT_NAME) if data else DEFAULT_NAME

    return dedent(f"""\
        ℹ️ INFORMACIÓN DE TU CONSULTA

        Hola *{name}*,
        Gracias por tu interés en nuestros servicios de crédito.
        En este momento no cuentas con una línea de crédito disponible.

        💡 ¿Cómo puedo calificar?
        - Mantén tus pagos al día
        - Continúa usando nuestro servicio regularmente
        - Evaluamos periódicamente a nuestros clientes

        📞 Para más información: {PHONE_NUMBER}
    """).strip()


def _format_error_message() -> str:
    """Format error message."""
    return dedent(f"""\
        ⚠️ INFORMACIÓN

        Hola {DEFAULT_NAME},
        En este momento no podemos procesar tu consulta.

        ¡Gracias por tu comprensión!
    """).strip()
