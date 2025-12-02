"""
Adaptadores para convertir las respuestas de cada cliente al formato estándar.
Implementan el patrón Adapter para desacoplar los clientes del servicio.
"""

import logging
from typing import Tuple, Dict, Any, Optional

from .query_service import (
    ResultadoConsulta,
    Canal,
    EstadoConsulta,
    ConsultorCanal,
)

logger = logging.getLogger(__name__)


class FNBAdapter:
    """
    Adaptador para el cliente FNB.
    Convierte las respuestas del cliente FNB al formato estándar ResultadoConsulta.
    """

    def __init__(self, get_session_func, consultar_dni_func):
        """
        Inicializar el adaptador con las funciones del cliente FNB.

        Args:
            get_session_func: Función para obtener la sesión autenticada
            consultar_dni_func: Función para consultar DNI en FNB
        """
        self._get_session = get_session_func
        self._consultar_dni = consultar_dni_func

    def consultar(self, dni: str) -> ResultadoConsulta:
        """
        Consultar DNI en FNB y convertir al formato estándar.

        Args:
            dni: DNI de 8 dígitos

        Returns:
            ResultadoConsulta estandarizado
        """
        try:
            session, id_aliado = self._get_session()
        except Exception as e:
            logger.error(f"Error obteniendo sesión FNB: {e}")
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=Canal.FNB,
                estado=EstadoConsulta.ERROR,
                mensaje_error=f"Error de autenticación: {str(e)}",
            )

        try:
            data, estado, mensaje_api = self._consultar_dni(session, dni, id_aliado)
            return self._convertir_respuesta(dni, data, estado, mensaje_api)
        except Exception as e:
            logger.error(f"Error consultando FNB: {e}")
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=Canal.FNB,
                estado=EstadoConsulta.ERROR,
                mensaje_error=str(e),
            )

    def _convertir_respuesta(
        self, dni: str, data: Optional[Dict], estado: str, mensaje_api: Optional[str]
    ) -> ResultadoConsulta:
        """Convertir respuesta FNB al formato estándar"""

        # Caso exitoso con datos
        if estado == "success" and data:
            tiene_credito = data.get("tieneLineaCredito", False)
            return ResultadoConsulta(
                exito=True,
                dni=dni,
                canal=Canal.FNB,
                datos=data,
                estado=(
                    EstadoConsulta.SUCCESS
                    if tiene_credito
                    else EstadoConsulta.NO_CREDIT
                ),
                tiene_oferta=tiene_credito,
            )

        # DNI no encontrado o sin campaña
        if estado.startswith("invalid:") or (
            mensaje_api and self._es_no_encontrado(mensaje_api)
        ):
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=Canal.FNB,
                estado=EstadoConsulta.NOT_FOUND,
                mensaje_error=mensaje_api,
            )

        # Error genérico
        return ResultadoConsulta(
            exito=False,
            dni=dni,
            canal=Canal.FNB,
            estado=EstadoConsulta.ERROR,
            mensaje_error=mensaje_api or estado,
        )

    def _es_no_encontrado(self, mensaje: str) -> bool:
        """Verificar si el mensaje indica que el cliente no fue encontrado"""
        mensaje_lower = mensaje.lower()
        indicadores = ["no encontrado", "no existe", "no califica", "no tiene campaña"]
        return any(ind in mensaje_lower for ind in indicadores)


class GASOAdapter:
    """
    Adaptador para el cliente GASO (Power BI).
    Convierte las respuestas del cliente GASO al formato estándar ResultadoConsulta.
    """

    def __init__(self, consultar_dni_gaso_func):
        """
        Inicializar el adaptador con la función de consulta GASO.

        Args:
            consultar_dni_gaso_func: Función para consultar DNI en GASO
        """
        self._consultar_dni_gaso = consultar_dni_gaso_func

    def consultar(self, dni: str) -> ResultadoConsulta:
        """
        Consultar DNI en GASO y convertir al formato estándar.

        Args:
            dni: DNI de 8 dígitos

        Returns:
            ResultadoConsulta estandarizado
        """
        try:
            data, estado, mensaje_api = self._consultar_dni_gaso(dni)
            return self._convertir_respuesta(dni, data, estado, mensaje_api)
        except Exception as e:
            logger.error(f"Error consultando GASO: {e}")
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=Canal.GASO,
                estado=EstadoConsulta.ERROR,
                mensaje_error=str(e),
            )

    def _convertir_respuesta(
        self, dni: str, data: Optional[Dict], estado: str, mensaje_api: Optional[str]
    ) -> ResultadoConsulta:
        """Convertir respuesta GASO al formato estándar"""

        # Caso exitoso con datos
        if estado == "success" and data:
            tiene_credito = data.get("tieneLineaCredito", False)
            return ResultadoConsulta(
                exito=True,
                dni=dni,
                canal=Canal.GASO,
                datos=data,
                estado=(
                    EstadoConsulta.SUCCESS
                    if tiene_credito
                    else EstadoConsulta.NO_CREDIT
                ),
                tiene_oferta=tiene_credito,
            )

        # No encontrado
        if estado == "not_found":
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=Canal.GASO,
                estado=EstadoConsulta.NOT_FOUND,
                mensaje_error=mensaje_api,
            )

        # Error
        return ResultadoConsulta(
            exito=False,
            dni=dni,
            canal=Canal.GASO,
            estado=EstadoConsulta.ERROR,
            mensaje_error=mensaje_api or estado,
        )


def crear_consultor_fnb(get_session_func, consultar_dni_func) -> ConsultorCanal:
    """
    Factory para crear un consultor FNB compatible con QueryService.

    Args:
        get_session_func: Función para obtener sesión
        consultar_dni_func: Función para consultar DNI

    Returns:
        Función consultora que cumple con el tipo ConsultorCanal
    """
    adapter = FNBAdapter(get_session_func, consultar_dni_func)
    return adapter.consultar


def crear_consultor_gaso(consultar_dni_gaso_func) -> ConsultorCanal:
    """
    Factory para crear un consultor GASO compatible con QueryService.

    Args:
        consultar_dni_gaso_func: Función para consultar DNI en GASO

    Returns:
        Función consultora que cumple con el tipo ConsultorCanal
    """
    adapter = GASOAdapter(consultar_dni_gaso_func)
    return adapter.consultar
