"""
Generador de mensajes para respuestas al cliente.
Convierte ResultadoConsulta en mensajes amigables para Chatwoot.
"""

import textwrap
from typing import Tuple, Optional, Dict, Any

from .query_service import ResultadoConsulta, EstadoConsulta


class MessageGenerator:
    """
    Generador de mensajes personalizados basados en el resultado de la consulta.

    Responsabilidad única: Convertir ResultadoConsulta en mensajes para el usuario.
    """

    @staticmethod
    def generar(resultado: ResultadoConsulta) -> Tuple[str, bool]:
        """
        Generar mensaje personalizado según el resultado de la consulta.

        Args:
            resultado: ResultadoConsulta de la consulta

        Returns:
            Tupla (mensaje_completo, tiene_oferta)
        """
        if resultado.estado == EstadoConsulta.SUCCESS and resultado.tiene_oferta:
            return MessageGenerator._mensaje_con_oferta(resultado.datos)

        if resultado.estado == EstadoConsulta.NO_CREDIT:
            return MessageGenerator._mensaje_sin_credito(resultado.datos)

        if resultado.estado == EstadoConsulta.NOT_FOUND:
            return MessageGenerator._mensaje_no_encontrado()

        # Error u otro caso
        return MessageGenerator._mensaje_error()

    @staticmethod
    def _mensaje_con_oferta(datos: Optional[Dict[str, Any]]) -> Tuple[str, bool]:
        """Mensaje para cliente CON línea de crédito aprobada"""
        datos = datos or {}
        nombre = datos.get("nombre", "Cliente")
        monto = datos.get("lineaCredito", 0)

        # Manejar el caso de GASO donde viene 'saldo' en vez de 'lineaCredito'
        if monto == 0 and "saldo" in datos:
            try:
                monto = float(datos["saldo"])
            except (ValueError, TypeError):
                monto = 0

        mensaje = textwrap.dedent(
            f"""
            🎉 ¡FELICITACIONES!
                                           
            Hola *{nombre}*,
            ¡Tenemos excelentes noticias para ti!
                                           
            Tienes una línea de crédito APROBADA por:
            💰 S/ {monto:,.2f} soles !!!
                                           
        """
        ).strip()

        return mensaje, True

    @staticmethod
    def _mensaje_sin_credito(datos: Optional[Dict[str, Any]]) -> Tuple[str, bool]:
        """Mensaje para cliente registrado pero SIN línea de crédito"""
        datos = datos or {}
        nombre = datos.get("nombre", "Cliente")

        mensaje = textwrap.dedent(
            f"""
            ℹ️ INFORMACIÓN DE TU CONSULTA
                                           
            Hola *{nombre}*,
            Gracias por tu interés en nuestros servicios de crédito.
            En este momento no cuentas con una línea de crédito disponible.
                                           
            💡 ¿Cómo puedo calificar?
               • Mantén tus pagos al día.
               • Continúa usando nuestro servicio regularmente.
               • Evaluamos periódicamente a nuestros clientes.
                                           
            Sigue usando el servicio de Calidda y muy pronto podrías calificar para una oferta crediticia.

            📞 Para más información, comunícate con nuestro centro de atención al cliente al 01-614-9000 opc 3.
            
            ¡Hasta luego!
        """
        ).strip()

        return mensaje, False

    @staticmethod
    def _mensaje_no_encontrado() -> Tuple[str, bool]:
        """Mensaje para DNI no encontrado o sin campaña activa"""
        mensaje = textwrap.dedent(
            """
            ℹ️ INFORMACIÓN DE TU CONSULTA
                                           
            Gracias por tu interés en nuestros servicios de crédito.
            En este momento no cuentas con una línea de crédito disponible.
                                           
            💡 ¿Cómo puedo calificar?
               • Mantén tus pagos al día.
               • Continúa usando nuestro servicio regularmente.
               • Evaluamos periódicamente a nuestros clientes.
                                           
            Sigue usando el servicio de Calidda y muy pronto podrías calificar para una oferta crediticia.

            📞 Para más información, comunícate con nuestro centro de atención al cliente al 01-614-9000 opc 3.
                                           
            ¡Hasta luego!
        """
        ).strip()

        return mensaje, False

    @staticmethod
    def _mensaje_error() -> Tuple[str, bool]:
        """Mensaje para error genérico"""
        mensaje = textwrap.dedent(
            """
            ⚠️ INFORMACIÓN
                                           
            Hola Cliente,
            En este momento no podemos procesar tu consulta.
                                           
            ¡Gracias por tu comprensión!
        """
        ).strip()

        return mensaje, False
