#!/usr/bin/env python3
"""
FastAPI wrapper para consulta de líneas de crédito en Calidda.

Arquitectura:
- Flujo de fallback: FNB → GASO (si no encuentra en FNB, intenta en GASO)
- Alta cohesión: Cada componente tiene una responsabilidad clara
- Bajo acoplamiento: Los canales son independientes y se conectan via adaptadores

Endpoints:
- POST /query         : Consulta con fallback automático (FNB → GASO)
- POST /query/fnb     : Consulta solo en FNB
- POST /query/gaso    : Consulta solo en GASO
- GET  /health        : Health check general
"""

import os
import sys
from typing import Optional, Dict, Any
from enum import Enum

# Configurar paths
ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import uvicorn
import time
import threading
import logging

# Importar componentes internos
from vcc_totem.api.auth import login
from vcc_totem.api.client import consultar_dni
from vcc_totem.api.gaso_client import consultar_dni_gaso, verificar_conexion_gaso
from vcc_totem.services import (
    QueryService,
    Canal,
    EstadoConsulta,
    ConfiguracionFallback,
    crear_consultor_fnb,
    crear_consultor_gaso,
    MessageGenerator,
    ResultadoConsulta,
)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN DE SESIÓN FNB
# ============================================================================

SESSION_TTL = int(os.environ.get("CALIDDA_SESSION_TTL", 3600))  # 1 hora por defecto

_session_lock = threading.Lock()
_session_cache = {
    "session": None,
    "id_aliado": None,
    "ts": 0,
}


def get_session(force: bool = False):
    """
    Obtener sesión autenticada de FNB con cache.

    Args:
        force: Si es True, fuerza un nuevo login

    Returns:
        Tupla (session, id_aliado)

    Raises:
        RuntimeError: Si no se puede autenticar
    """
    now = time.time()

    # Fast path: sesión válida en cache
    sess = _session_cache.get("session")
    if not force and sess and (now - _session_cache.get("ts", 0) < SESSION_TTL):
        return sess, _session_cache.get("id_aliado")

    # Adquirir lock para login único entre threads
    with _session_lock:
        # Verificar de nuevo después de adquirir lock
        sess = _session_cache.get("session")
        if (
            not force
            and sess
            and (time.time() - _session_cache.get("ts", 0) < SESSION_TTL)
        ):
            return sess, _session_cache.get("id_aliado")

        # Realizar login
        s, id_aliado = login()
        if not s:
            _session_cache["ts"] = 0
            raise RuntimeError("No se pudo iniciar sesión en Calidda FNB")

        _session_cache["session"] = s
        _session_cache["id_aliado"] = id_aliado
        _session_cache["ts"] = time.time()
        return s, id_aliado


def invalidar_sesion():
    """Invalidar la sesión cacheada para forzar re-login en próxima consulta"""
    _session_cache["ts"] = 0


# ============================================================================
# INICIALIZACIÓN DEL SERVICIO DE CONSULTAS
# ============================================================================


def crear_query_service() -> QueryService:
    """
    Factory para crear el servicio de consultas con todos los adaptadores configurados.

    Returns:
        QueryService configurado con FNB y GASO
    """
    # Configuración de fallback: primero FNB, luego GASO
    config = ConfiguracionFallback(
        canales_orden=[Canal.FNB, Canal.GASO], continuar_en_error=True
    )

    service = QueryService(config)

    # Registrar consultor FNB
    consultor_fnb = crear_consultor_fnb(get_session, consultar_dni)
    service.registrar_consultor(Canal.FNB, consultor_fnb)

    # Registrar consultor GASO
    consultor_gaso = crear_consultor_gaso(consultar_dni_gaso)
    service.registrar_consultor(Canal.GASO, consultor_gaso)

    return service


# Instancia global del servicio
query_service = crear_query_service()


# ============================================================================
# MODELOS DE REQUEST/RESPONSE
# ============================================================================


class CanalEnum(str, Enum):
    """Canales disponibles para consulta directa"""

    FNB = "fnb"
    GASO = "gaso"


class DNIRequest(BaseModel):
    """Request para consulta de DNI"""

    dni: str = Field(
        ...,
        min_length=8,
        max_length=8,
        description="DNI de 8 dígitos",
        json_schema_extra={"example": "12345678"},
    )


class QueryResponse(BaseModel):
    """Response estandarizada de consulta"""

    success: bool = Field(description="Indica si la consulta fue exitosa")
    dni: str = Field(description="DNI consultado")
    canal: str = Field(description="Canal donde se encontró el resultado (fnb/gaso)")
    client_message: Optional[str] = Field(
        description="Mensaje formateado para el cliente"
    )
    error: Optional[str] = Field(default=None, description="Mensaje de error si aplica")
    return_code: int = Field(
        description="Código de retorno: 0=éxito, 1=no encontrado, 2=error"
    )
    tiene_oferta: bool = Field(
        default=False, description="Indica si el cliente tiene oferta de crédito"
    )
    datos: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Datos completos del cliente (nombre, dirección, saldo, etc.)",
    )


# ============================================================================
# FUNCIONES DE CONVERSIÓN
# ============================================================================


def resultado_a_response(resultado: ResultadoConsulta) -> QueryResponse:
    """
    Convertir ResultadoConsulta a QueryResponse para la API.

    Args:
        resultado: Resultado de la consulta del servicio

    Returns:
        QueryResponse para enviar al cliente
    """
    # Generar mensaje personalizado
    mensaje, tiene_oferta = MessageGenerator.generar(resultado)

    # Determinar código de retorno
    if resultado.estado == EstadoConsulta.SUCCESS:
        return_code = 0
    elif resultado.estado in (EstadoConsulta.NOT_FOUND, EstadoConsulta.NO_CREDIT):
        return_code = 1
    else:
        return_code = 2

    return QueryResponse(
        success=resultado.cliente_encontrado
        or resultado.estado == EstadoConsulta.NO_CREDIT,
        dni=resultado.dni,
        canal=resultado.canal.value,
        client_message=mensaje,
        error=resultado.mensaje_error if not resultado.exito else None,
        return_code=return_code,
        tiene_oferta=tiene_oferta,
        datos=resultado.datos,
    )


# ============================================================================
# APLICACIÓN FASTAPI
# ============================================================================

app = FastAPI(
    title="Calidda Credit API",
    version="3.0",
    description="""
API para consultar líneas de crédito en los sistemas de Calidda.

## Flujo de consulta

1. **Endpoint principal `/query`**: Consulta primero en FNB, si no encuentra datos intenta en GASO.
2. **Endpoints específicos**: `/query/fnb` y `/query/gaso` para consultar un canal específico.

## Canales

- **FNB**: Sistema principal con autenticación (API REST)
- **GASO**: Sistema secundario via Power BI (API pública)
    """,
    contact={"name": "Diego Moscaiza"},
)


@app.get("/health")
def health():
    """Health check del servicio"""
    return {
        "status": "ok",
        "version": "3.0",
        "canales": {"fnb": "disponible", "gaso": "disponible"},
    }


@app.get("/health/gaso")
def health_gaso():
    """Verificar conexión específica con GASO (Power BI)"""
    conectado = verificar_conexion_gaso()
    return {
        "status": "ok" if conectado else "error",
        "canal": "gaso",
        "powerbi": "conectado" if conectado else "sin conexión",
    }


@app.post("/query", response_model=QueryResponse)
def query_dni(body: DNIRequest):
    """
    Consultar DNI con fallback automático (FNB → GASO).

    Flujo:
    1. Intenta consultar en FNB
    2. Si no encuentra datos, intenta en GASO
    3. Retorna el primer resultado exitoso o el error del último canal

    Args:
        body: Request con el DNI de 8 dígitos

    Returns:
        QueryResponse con el resultado de la consulta
    """
    dni = body.dni.strip()

    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(
            status_code=400, detail="DNI inválido: debe contener 8 dígitos numéricos"
        )

    try:
        resultado = query_service.consultar(dni)
        return resultado_a_response(resultado)
    except Exception as e:
        logger.error(f"Error en consulta: {e}")
        invalidar_sesion()  # Invalidar sesión por si el error fue de autenticación
        raise HTTPException(
            status_code=500, detail=f"Error procesando consulta: {str(e)}"
        )


@app.post("/query/fnb", response_model=QueryResponse)
def query_fnb(body: DNIRequest):
    """
    Consultar DNI solo en canal FNB (sin fallback).

    Args:
        body: Request con el DNI de 8 dígitos

    Returns:
        QueryResponse con el resultado de la consulta en FNB
    """
    dni = body.dni.strip()

    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(
            status_code=400, detail="DNI inválido: debe contener 8 dígitos numéricos"
        )

    try:
        resultado = query_service.consultar_canal_especifico(dni, Canal.FNB)
        return resultado_a_response(resultado)
    except Exception as e:
        logger.error(f"Error en consulta FNB: {e}")
        invalidar_sesion()
        raise HTTPException(status_code=500, detail=f"Error consultando FNB: {str(e)}")


@app.post("/query/gaso", response_model=QueryResponse)
def query_gaso(body: DNIRequest):
    """
    Consultar DNI solo en canal GASO (sin fallback).

    Args:
        body: Request con el DNI de 8 dígitos

    Returns:
        QueryResponse con el resultado de la consulta en GASO
    """
    dni = body.dni.strip()

    if not dni.isdigit() or len(dni) != 8:
        raise HTTPException(
            status_code=400, detail="DNI inválido: debe contener 8 dígitos numéricos"
        )

    try:
        resultado = query_service.consultar_canal_especifico(dni, Canal.GASO)
        return resultado_a_response(resultado)
    except Exception as e:
        logger.error(f"Error en consulta GASO: {e}")
        raise HTTPException(status_code=500, detail=f"Error consultando GASO: {str(e)}")


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    uvicorn.run("api_wrapper:app", host="0.0.0.0", port=5000, log_level="info")
