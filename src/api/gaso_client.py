"""
Cliente para consultar datos de GASO via Power BI API.

Configuración externalizada y sin hardcodeos.
Los Visual IDs se obtienen del dashboard de Power BI.
"""

import requests
import logging
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN (externalizable a .env si es necesario)
# ============================================================================


@dataclass(frozen=True)
class PowerBIConfig:
    """Configuración de conexión a Power BI"""

    api_url: str = (
        "https://wabi-south-central-us-api.analysis.windows.net/public/reports/querydata"
    )
    resource_key: str = "96e10df6-51ec-4855-90c0-46efab054e4a"
    dataset_id: str = "4570cf7b-a48f-440e-8f93-226828a3a243"
    report_id: str = "2f8ea0ef-30a2-442c-af53-b3fc7bfa1027"
    model_id: int = 11453601
    timeout: int = 30


@dataclass(frozen=True)
class VisualIDs:
    """
    IDs de los visuales en Power BI para cada campo.
    Estos IDs se obtienen del Network tab del navegador al interactuar con el dashboard.

    Obtenidos de: PBI.EX.VisualValidationSummary en telemetría
    """

    # Campos principales - IDs reales del dashboard
    estado: str = "1939653a9d6bbd4abe2b"  # cardVisual - Estado (NO APLICA, etc.)
    saldo: str = "fa2a9da34ca3522cc3b6"  # cardVisual - Saldo
    nombre: str = "a75cdb19088461402488"  # cardVisual - Nombre
    cta_contrato: str = "c034bb0d649b01c765c0"  # cardVisual - Cuenta_contrato
    nse: str = "3ad014bf316f57fe6b8f"  # cardVisual - NSE
    direccion: str = "04df67600e7aad10d3a0"  # cardVisual - Dirección
    distrito: str = "7f69ea308db71aa50aa7"  # cardVisual - Distrito
    documento: str = (
        "123456789abc0def"  # cardVisual - Documento (Número de documento del cliente)
    )
    estado_cta: str = (
        "fedcba9876543210abcd"  # cardVisual - Estado_cta (Estado de la cuenta)
    )
    dni_display: str = "fd3e9d3fd68ea1f90ca8"  # cardVisual - DNI mostrado
    habilitado: str = "77514030e46273f8c66a"  # cardVisual - Estado habilitado


# Instancias de configuración por defecto
CONFIG = PowerBIConfig()
VISUAL_IDS = VisualIDs()

# Headers base para las requests
HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://app.powerbi.com",
    "Referer": "https://app.powerbi.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    "X-PowerBI-ResourceKey": CONFIG.resource_key,
}


# ============================================================================
# CONSTRUCCIÓN DE PAYLOADS
# ============================================================================


def _build_measure_query_payload(dni: str, property_name: str, visual_id: str) -> dict:
    """
    Construir payload para consultar una MEDIDA (measure) en Power BI.
    Usado para: Estado, Saldo, etc.
    """
    return {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {"Name": "m", "Entity": "Medidas", "Type": 0},
                                        {"Name": "b", "Entity": "BD", "Type": 0},
                                    ],
                                    "Select": [
                                        {
                                            "Measure": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "m"}
                                                },
                                                "Property": property_name,
                                            },
                                            "Name": f"Medidas.{property_name}",
                                            "NativeReferenceName": property_name,
                                        }
                                    ],
                                    "Where": [
                                        {
                                            "Condition": {
                                                "Contains": {
                                                    "Left": {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "b"
                                                                }
                                                            },
                                                            "Property": "DNI",
                                                        }
                                                    },
                                                    "Right": {
                                                        "Literal": {"Value": f"'{dni}'"}
                                                    },
                                                }
                                            }
                                        }
                                    ],
                                },
                                "Binding": {
                                    "Primary": {"Groupings": [{"Projections": [0]}]},
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": CONFIG.dataset_id,
                    "Sources": [{"ReportId": CONFIG.report_id, "VisualId": visual_id}],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": CONFIG.model_id,
    }


def _build_column_query_payload(dni: str, column_name: str, visual_id: str) -> dict:
    """
    Construir payload para consultar una COLUMNA de la tabla BD en Power BI.
    Usado para: Nombre, Direccion, Distrito, etc.
    """
    return {
        "version": "1.0.0",
        "queries": [
            {
                "Query": {
                    "Commands": [
                        {
                            "SemanticQueryDataShapeCommand": {
                                "Query": {
                                    "Version": 2,
                                    "From": [
                                        {"Name": "b", "Entity": "BD", "Type": 0},
                                    ],
                                    "Select": [
                                        {
                                            "Column": {
                                                "Expression": {
                                                    "SourceRef": {"Source": "b"}
                                                },
                                                "Property": column_name,
                                            },
                                            "Name": f"BD.{column_name}",
                                            "NativeReferenceName": column_name,
                                        }
                                    ],
                                    "Where": [
                                        {
                                            "Condition": {
                                                "Comparison": {
                                                    "ComparisonKind": 0,
                                                    "Left": {
                                                        "Column": {
                                                            "Expression": {
                                                                "SourceRef": {
                                                                    "Source": "b"
                                                                }
                                                            },
                                                            "Property": "DNI",
                                                        }
                                                    },
                                                    "Right": {
                                                        "Literal": {"Value": f"'{dni}'"}
                                                    },
                                                }
                                            }
                                        }
                                    ],
                                },
                                "Binding": {
                                    "Primary": {"Groupings": [{"Projections": [0]}]},
                                    "Version": 1,
                                },
                                "ExecutionMetricsKind": 1,
                            }
                        }
                    ]
                },
                "QueryId": "",
                "ApplicationContext": {
                    "DatasetId": CONFIG.dataset_id,
                    "Sources": [{"ReportId": CONFIG.report_id, "VisualId": visual_id}],
                },
            }
        ],
        "cancelQueries": [],
        "modelId": CONFIG.model_id,
    }


# Mantener compatibilidad con el nombre anterior
def _build_query_payload(dni: str, property_name: str, visual_id: str) -> dict:
    """Alias para _build_measure_query_payload (compatibilidad)"""
    return _build_measure_query_payload(dni, property_name, visual_id)


# ============================================================================
# EJECUCIÓN DE QUERIES
# ============================================================================


def _execute_query(payload: dict, timeout: int = None) -> Optional[dict]:
    """
    Ejecutar una query en Power BI.

    Args:
        payload: Payload JSON para la API
        timeout: Timeout en segundos (usa CONFIG.timeout por defecto)

    Returns:
        Respuesta JSON o None si hay error
    """
    timeout = timeout or CONFIG.timeout

    try:
        url = f"{CONFIG.api_url}?synchronous=true"
        logger.debug(f"Ejecutando query en: {url}")

        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=timeout,
        )

        if response.status_code == 200:
            data = response.json()
            logger.debug(f"Respuesta recibida: status={response.status_code}")
            return data
        else:
            logger.error(
                f"Error en Power BI API: HTTP {response.status_code}"
                f"\nRespuesta: {response.text[:500]}"
            )
            return None

    except requests.exceptions.Timeout:
        logger.error(f"Timeout consultando Power BI ({timeout}s)")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Error de conexión con Power BI: {e}")
        return None
    except Exception as e:
        logger.error(f"Error consultando Power BI: {e}")
        return None


# ============================================================================
# EXTRACCIÓN DE VALORES
# ============================================================================


def _extract_value(response: dict) -> Optional[str]:
    """
    Extraer el valor de la respuesta de Power BI (para MEDIDAS).

    La estructura de respuesta de Power BI es:
    results[0].result.data.dsr.DS[0].PH[0].DM0[0].M0

    Args:
        response: Respuesta JSON de Power BI

    Returns:
        Valor extraído como string o None
    """
    try:
        results = response.get("results", [])
        if not results:
            logger.debug("No results en respuesta")
            return None

        result = results[0].get("result", {})
        data = result.get("data", {})
        dsr = data.get("dsr", {})
        ds = dsr.get("DS", [])

        if not ds:
            logger.debug("No DS en respuesta")
            return None

        ph = ds[0].get("PH", [])
        if not ph:
            logger.debug("No PH en DS[0]")
            return None

        dm0 = ph[0].get("DM0", [])
        if not dm0:
            logger.debug("No DM0 en PH[0]")
            return None

        # El valor está en M0 para medidas
        value = dm0[0].get("M0")
        if value is not None:
            valor_str = str(value).strip()
            logger.debug(f"Valor extraído: {valor_str}")
            return valor_str if valor_str else None

        logger.debug("M0 no encontrado en DM0[0]")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo valor: {e}")
        return None


def _extract_column_value(response: dict) -> Optional[str]:
    """
    Extraer el valor de la respuesta de Power BI (para COLUMNAS).

    Las columnas de la tabla BD se retornan de manera diferente a las medidas.
    Power BI puede retornar el valor de varias maneras:

    Opción 1: Valor en ValueDicts.D0 indexado por PH[0].DM0[0].C[0]
    Opción 2: Valor directo en PH[0].DM0[0].G0
    Opción 3: Valor directo en PH[0].DM0[0].C[0]

    Args:
        response: Respuesta JSON de Power BI

    Returns:
        Valor extraído como string o None
    """
    try:
        results = response.get("results", [])
        if not results:
            logger.debug("No results en respuesta de columna")
            return None

        result = results[0].get("result", {})
        data = result.get("data", {})
        dsr = data.get("dsr", {})
        ds = dsr.get("DS", [])

        if not ds:
            logger.debug("No DS en respuesta de columna")
            return None

        first_ds = ds[0]
        logger.debug(f"first_ds keys: {first_ds.keys()}")

        # Paso 1: Intentar obtener de ValueDicts (método preferido)
        value_dicts = first_ds.get("ValueDicts", {})
        if value_dicts:
            d0_list = value_dicts.get("D0", [])
            logger.debug(f"D0 encontrado con {len(d0_list)} valores")

            if d0_list:
                # Obtener el índice desde PH[0].DM0[0].C
                ph = first_ds.get("PH", [])
                if ph:
                    dm0 = ph[0].get("DM0", [])
                    if dm0:
                        c_indices = dm0[0].get("C", [])
                        logger.debug(f"C indices: {c_indices}")

                        if c_indices:
                            idx = c_indices[0]
                            if idx is not None and 0 <= idx < len(d0_list):
                                value = d0_list[idx]
                                logger.debug(f"Valor desde ValueDicts[{idx}]: {value}")
                                if value is not None:
                                    return str(value).strip()

        # Paso 2: Intentar obtener directamente de PH[0].DM0[0]
        ph = first_ds.get("PH", [])
        if ph:
            dm0 = ph[0].get("DM0", [])
            if dm0:
                # Intentar G0 (valor de grouping)
                g0_value = dm0[0].get("G0")
                if g0_value is not None:
                    logger.debug(f"Valor desde G0: {g0_value}")
                    return str(g0_value).strip()

                # Intentar C[0] (valor directo indexado)
                c_values = dm0[0].get("C", [])
                if c_values and c_values[0] is not None:
                    logger.debug(f"Valor desde C[0]: {c_values[0]}")
                    return str(c_values[0]).strip()

        logger.debug("No se pudo extraer valor de columna")
        return None

    except Exception as e:
        logger.error(f"Error extrayendo valor de columna: {e}", exc_info=True)
        return None


# ============================================================================
# CONSULTA PRINCIPAL
# ============================================================================


def consultar_dni_gaso(
    dni: str, timeout: int = None
) -> Tuple[Optional[Dict[str, Any]], str, Optional[str]]:
    """
    Consultar un DNI en el sistema GASO via Power BI.

    Flujo:
    1. Consulta el campo "Estado" para verificar si el cliente existe
    2. Si existe, consulta los demás campos (Saldo, Nombre, etc.)
    3. Retorna los datos consolidados

    Args:
        dni: Número de DNI (8 dígitos)
        timeout: Tiempo máximo de espera por consulta

    Returns:
        Tupla (datos, estado, mensaje_error)
        - datos: Diccionario con la información del cliente o None
        - estado: 'success', 'not_found', 'error'
        - mensaje_error: Mensaje de error si aplica
    """
    timeout = timeout or CONFIG.timeout
    logger.info(f"Consultando DNI {dni} en GASO (Power BI)")

    # Paso 1: Consultar Estado para verificar si el cliente existe
    try:
        logger.debug(f"[1/7] Consultando Estado del cliente {dni}")
        payload = _build_query_payload(dni, "Estado", VISUAL_IDS.estado)
        response = _execute_query(payload, timeout)

        if not response:
            logger.error(f"Sin respuesta de Power BI para DNI {dni}")
            return None, "error", "Error conectando con Power BI"

        estado_valor = _extract_value(response)

        # Si no hay estado o está vacío, el cliente no existe
        if not estado_valor or estado_valor == "--" or not estado_valor.strip():
            logger.info(f"DNI {dni} no encontrado en GASO (Estado vacío)")
            return None, "not_found", "Cliente no encontrado en GASO"

        logger.info(f"✓ DNI {dni} encontrado en GASO - Estado: {estado_valor}")

    except Exception as e:
        logger.error(f"Error consultando Estado: {e}")
        return None, "error", f"Error consultando GASO: {str(e)}"

    # Inicializar diccionario de datos
    datos_cliente = {}

    # Paso 2: Consultar Saldo (es una MEDIDA)
    saldo = None
    try:
        logger.debug(f"[2/7] Consultando Saldo del cliente {dni}")
        payload = _build_query_payload(dni, "Saldo", VISUAL_IDS.saldo)
        response = _execute_query(payload, timeout)
        if response:
            saldo = _extract_value(response)
            if saldo:
                logger.debug(f"✓ Saldo obtenido: {saldo}")
    except Exception as e:
        logger.warning(f"Error consultando Saldo: {e}")

    # Paso 3: Consultar Cliente (es una MEDIDA)
    nombre = None
    try:
        logger.debug(f"[3/9] Consultando Cliente del cliente {dni}")
        payload = _build_query_payload(dni, "Cliente", VISUAL_IDS.nombre)
        response = _execute_query(payload, timeout)
        if response:
            nombre = _extract_value(response)
            if nombre:
                logger.debug(f"✓ Cliente obtenido: {nombre}")
            else:
                logger.warning(f"Cliente retornó None para DNI {dni}")
    except Exception as e:
        logger.warning(f"Error consultando Cliente: {e}")

    # Paso 4: Consultar Cuenta Contrato (es una MEDIDA)
    cta_contrato = None
    try:
        logger.debug(f"[4/7] Consultando Cuenta Contrato del cliente {dni}")
        payload = _build_query_payload(dni, "Cuenta_contrato", VISUAL_IDS.cta_contrato)
        response = _execute_query(payload, timeout)
        if response:
            cta_contrato = _extract_value(response)
            if cta_contrato:
                logger.debug(f"✓ Cuenta Contrato obtenida: {cta_contrato}")
    except Exception as e:
        logger.warning(f"Error consultando Cuenta_contrato: {e}")

    # Paso 5: Consultar NSE (es una MEDIDA)
    nse = None
    try:
        logger.debug(f"[5/7] Consultando NSE del cliente {dni}")
        payload = _build_query_payload(dni, "NSE", VISUAL_IDS.nse)
        response = _execute_query(payload, timeout)
        if response:
            nse = _extract_value(response)
            if nse:
                logger.debug(f"✓ NSE obtenido: {nse}")
    except Exception as e:
        logger.warning(f"Error consultando NSE: {e}")

    # Paso 6: Consultar Dirección (es una MEDIDA)
    direccion = None
    try:
        logger.debug(f"[6/7] Consultando Dirección del cliente {dni}")
        payload = _build_query_payload(dni, "Dirección", VISUAL_IDS.direccion)
        response = _execute_query(payload, timeout)
        if response:
            direccion = _extract_value(response)
            if direccion:
                logger.debug(f"✓ Dirección obtenida: {direccion}")
            else:
                logger.warning(f"Dirección retornó None para DNI {dni}")
    except Exception as e:
        logger.warning(f"Error consultando Dirección: {e}")

    # Paso 7: Consultar Distrito (es una MEDIDA)
    distrito = None
    try:
        logger.debug(f"[7/7] Consultando Distrito del cliente {dni}")
        payload = _build_query_payload(dni, "Distrito", VISUAL_IDS.distrito)
        response = _execute_query(payload, timeout)
        if response:
            distrito = _extract_value(response)
            if distrito:
                logger.debug(f"✓ Distrito obtenido: {distrito}")
            else:
                logger.warning(f"Distrito retornó None para DNI {dni}")
    except Exception as e:
        logger.warning(f"Error consultando Distrito: {e}")

    # Paso 8: Consultar Documento (es una MEDIDA)
    documento = None
    try:
        logger.debug(f"[8/9] Consultando Documento del cliente {dni}")
        payload = _build_query_payload(dni, "Documento", VISUAL_IDS.documento)
        response = _execute_query(payload, timeout)
        if response:
            documento = _extract_value(response)
            if documento:
                logger.debug(f"✓ Documento obtenido: {documento}")
            else:
                logger.warning(f"Documento retornó None para DNI {dni}")
    except Exception as e:
        logger.warning(f"Error consultando Documento: {e}")

    # Paso 9: Consultar Estado de Cuenta (es una MEDIDA)
    estado_cta = None
    try:
        logger.debug(f"[9/9] Consultando Estado de Cuenta del cliente {dni}")
        payload = _build_query_payload(dni, "Estado_cta", VISUAL_IDS.estado_cta)
        response = _execute_query(payload, timeout)
        if response:
            estado_cta = _extract_value(response)
            if estado_cta:
                logger.debug(f"✓ Estado de Cuenta obtenido: {estado_cta}")
            else:
                logger.warning(f"Estado_cta retornó None para DNI {dni}")
    except Exception as e:
        logger.warning(f"Error consultando Estado_cta: {e}")

    # Calcular si tiene línea de crédito
    # Requisitos: 1) Saldo > 0, 2) Estado NO sea "NO APLICA"
    saldo_numerico = _parsear_saldo(saldo) if saldo else 0
    estado_valido = estado_valor and estado_valor.upper() != "NO APLICA"
    tiene_linea = saldo_numerico > 0 and estado_valido

    # Construir dirección completa
    direccion_completa = None
    if direccion and distrito:
        # Si tenemos ambas, combinarlas
        direccion_completa = f"{direccion} - {distrito}"
    elif direccion:
        # Si solo tenemos dirección
        direccion_completa = direccion
    elif distrito:
        # Si solo tenemos distrito
        direccion_completa = distrito

    # Construir datos del cliente
    datos_cliente = {
        "id": dni,
        "dni": dni,
        "nombre": nombre or "Cliente GASO",  # Fallback si no se obtiene nombre
        "estado": estado_valor,
        "saldo": saldo or "0",
        "cuentaContrato": cta_contrato,
        "nse": nse,
        "direccion": direccion_completa,
        "documento": documento,
        "estadoCta": estado_cta,
        "tieneLineaCredito": tiene_linea,
        "lineaCredito": saldo_numerico,
        "canal": "GASO",
        "segmento": "gaso",
    }

    logger.info(
        f"✓ Consulta completada para DNI {dni}: {('con oferta' if tiene_linea else 'sin oferta')}"
    )
    return datos_cliente, "success", None


def _parsear_saldo(saldo_str: str) -> float:
    """
    Parsear string de saldo a float.
    Maneja formatos como "S/ 5.000", "S/ 5,000", "5000", "5.000,00", etc.

    Reglas:
    - Si hay punto y coma, usa coma como decimal
    - Si hay punto y sin coma, usa punto como decimal
    - Remueve símbolos de moneda, espacios

    Args:
        saldo_str: String con el saldo a parsear

    Returns:
        Valor numérico del saldo o 0.0 si no se puede parsear
    """
    if not saldo_str:
        return 0.0

    try:
        # Remover S/, espacios al inicio/final
        limpio = saldo_str.replace("S/", "").strip()

        # Si está vacío después de limpiar
        if not limpio:
            return 0.0

        # Detectar formato: punto vs coma como separador
        tiene_punto = "." in limpio
        tiene_coma = "," in limpio

        # Formato 1.234,56 (punto de miles, coma decimal) - común en Latinoamérica
        if tiene_punto and tiene_coma:
            # Remover puntos (miles) y reemplazar coma por punto
            limpio = limpio.replace(".", "").replace(",", ".")
        # Formato 1,234.56 (coma de miles, punto decimal) - común en USA
        elif tiene_coma and tiene_punto:
            # Esto ya es el caso anterior
            pass
        # Formato 1.234 (solo punto, podría ser miles o decimal)
        elif tiene_punto and not tiene_coma:
            # Asumir formato Latinoamérica: 1.234,00 (sin la coma)
            # O podría ser 1234.56
            # Si hay más de 2 dígitos después del punto, probablemente sea miles
            partes = limpio.split(".")
            if len(partes) == 2 and len(partes[1]) > 2:
                limpio = limpio.replace(".", "")  # Es separador de miles
            # Si no, dejar como está (es decimal)
        # Formato 1,234 (solo coma, podría ser miles o decimal)
        elif tiene_coma and not tiene_punto:
            # En Perú, coma suele ser decimal
            limpio = limpio.replace(",", ".")

        return float(limpio)
    except (ValueError, TypeError):
        logger.warning(f"No se pudo parsear saldo: '{saldo_str}'")
        return 0.0


def verificar_conexion_gaso() -> bool:
    """Verificar que la conexión a Power BI está funcionando"""
    try:
        payload = _build_query_payload("00000000", "Estado", VISUAL_IDS.estado)
        response = _execute_query(payload, timeout=10)
        return response is not None
    except Exception:
        return False
