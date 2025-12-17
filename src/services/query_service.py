"""
Servicio de consulta de DNI con estrategia de fallback.
Orquesta las consultas entre los diferentes canales (FNB, GASO).

Principios:
- Alta cohesión: Cada componente tiene una responsabilidad clara
- Bajo acoplamiento: Los canales son independientes entre sí
- Sin hardcodeos: Configuración externalizada
"""

import logging
from typing import Optional, List, Callable, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class Canal(str, Enum):
    """Canales disponibles para consulta"""

    FNB = "fnb"
    GASO = "gaso"


class EstadoConsulta(str, Enum):
    """Estados posibles de una consulta"""

    SUCCESS = "success"
    NOT_FOUND = "not_found"
    ERROR = "error"
    NO_CREDIT = "no_credit"


@dataclass
class ResultadoConsulta:
    """Resultado estandarizado de una consulta a cualquier canal"""

    exito: bool
    dni: str
    canal: Canal
    datos: Optional[Dict[str, Any]] = None
    estado: EstadoConsulta = EstadoConsulta.NOT_FOUND
    mensaje_error: Optional[str] = None
    tiene_oferta: bool = False

    @property
    def cliente_encontrado(self) -> bool:
        """Indica si se encontró al cliente con datos válidos"""
        return (
            self.exito
            and self.datos is not None
            and self.estado == EstadoConsulta.SUCCESS
        )


@dataclass
class ConfiguracionFallback:
    """Configuración para la estrategia de fallback"""

    canales_orden: List[Canal] = field(default_factory=lambda: [Canal.FNB, Canal.GASO])
    continuar_en_error: bool = True  # Si hay error en un canal, intentar el siguiente


# Tipo para las funciones de consulta de cada canal
ConsultorCanal = Callable[[str], ResultadoConsulta]


class QueryService:
    """
    Servicio que orquesta las consultas de DNI entre múltiples canales.

    Implementa el patrón Chain of Responsibility para el fallback.
    """

    def __init__(self, config: Optional[ConfiguracionFallback] = None):
        """
        Inicializar el servicio con la configuración de fallback.

        Args:
            config: Configuración de fallback. Si es None, usa valores por defecto.
        """
        self.config = config or ConfiguracionFallback()
        self._consultores: Dict[Canal, ConsultorCanal] = {}

    def registrar_consultor(self, canal: Canal, consultor: ConsultorCanal) -> None:
        """
        Registrar un consultor para un canal específico.

        Args:
            canal: El canal al que pertenece el consultor
            consultor: Función que realiza la consulta y retorna ResultadoConsulta
        """
        self._consultores[canal] = consultor
        logger.info(f"Consultor registrado para canal: {canal.value}")

    def consultar(self, dni: str) -> ResultadoConsulta:
        """
        Consultar un DNI siguiendo la estrategia de fallback.

        Flujo:
        1. Intenta consultar en el primer canal (FNB por defecto)
        2. Si no encuentra datos, intenta en el siguiente canal (GASO)
        3. Si ningún canal tiene datos, retorna el resultado del último canal

        Args:
            dni: DNI de 8 dígitos a consultar

        Returns:
            ResultadoConsulta con los datos del cliente o el error
        """
        ultimo_resultado: Optional[ResultadoConsulta] = None

        for canal in self.config.canales_orden:
            consultor = self._consultores.get(canal)

            if not consultor:
                logger.warning(f"No hay consultor registrado para canal: {canal.value}")
                continue

            try:
                logger.info(f"Consultando DNI {dni} en canal: {canal.value}")
                resultado = consultor(dni)
                ultimo_resultado = resultado

                # Si encontramos al cliente con éxito, retornamos inmediatamente
                if resultado.cliente_encontrado:
                    logger.info(f"DNI {dni} encontrado en canal: {canal.value}")
                    return resultado

                # Si no encontró datos pero no hubo error, continuamos al siguiente canal
                if resultado.estado == EstadoConsulta.NOT_FOUND:
                    logger.info(
                        f"DNI {dni} no encontrado en {canal.value}, intentando siguiente canal..."
                    )
                    continue

                # Si hay error y la config permite continuar, seguimos
                if (
                    resultado.estado == EstadoConsulta.ERROR
                    and self.config.continuar_en_error
                ):
                    logger.warning(
                        f"Error en {canal.value}, intentando siguiente canal..."
                    )
                    continue

            except Exception as e:
                logger.error(f"Excepción consultando {canal.value}: {e}")
                ultimo_resultado = ResultadoConsulta(
                    exito=False,
                    dni=dni,
                    canal=canal,
                    estado=EstadoConsulta.ERROR,
                    mensaje_error=str(e),
                )

                if self.config.continuar_en_error:
                    continue
                else:
                    return ultimo_resultado

        # Si llegamos aquí, ningún canal encontró al cliente
        # Retornamos el último resultado (o uno por defecto si no hay ninguno)
        if ultimo_resultado:
            return ultimo_resultado

        return ResultadoConsulta(
            exito=False,
            dni=dni,
            canal=(
                self.config.canales_orden[0] if self.config.canales_orden else Canal.FNB
            ),
            estado=EstadoConsulta.ERROR,
            mensaje_error="No hay canales configurados para consulta",
        )

    def consultar_canal_especifico(self, dni: str, canal: Canal) -> ResultadoConsulta:
        """
        Consultar un DNI en un canal específico sin fallback.

        Args:
            dni: DNI de 8 dígitos
            canal: Canal específico a consultar

        Returns:
            ResultadoConsulta
        """
        consultor = self._consultores.get(canal)

        if not consultor:
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=canal,
                estado=EstadoConsulta.ERROR,
                mensaje_error=f"No hay consultor registrado para canal: {canal.value}",
            )

        try:
            return consultor(dni)
        except Exception as e:
            logger.error(f"Error consultando {canal.value}: {e}")
            return ResultadoConsulta(
                exito=False,
                dni=dni,
                canal=canal,
                estado=EstadoConsulta.ERROR,
                mensaje_error=str(e),
            )
