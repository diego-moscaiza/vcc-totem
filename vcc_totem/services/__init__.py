"""
Módulo de servicios.
Expone los componentes principales para la orquestación de consultas.
"""

from .query_service import (
    QueryService,
    ResultadoConsulta,
    Canal,
    EstadoConsulta,
    ConfiguracionFallback,
)
from .adapters import (
    crear_consultor_fnb,
    crear_consultor_gaso,
    FNBAdapter,
    GASOAdapter,
)
from .message_generator import MessageGenerator

__all__ = [
    # Servicio principal
    "QueryService",
    # Modelos de datos
    "ResultadoConsulta",
    "Canal",
    "EstadoConsulta",
    "ConfiguracionFallback",
    # Factories de adaptadores
    "crear_consultor_fnb",
    "crear_consultor_gaso",
    # Clases de adaptadores (para testing)
    "FNBAdapter",
    "GASOAdapter",
    # Generador de mensajes
    "MessageGenerator",
]
