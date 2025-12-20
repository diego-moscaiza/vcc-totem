import requests
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PowerBIConfig:
    api_url: str = "https://wabi-south-central-us-api.analysis.windows.net/public/reports/querydata"
    resource_key: str = "96e10df6-51ec-4855-90c0-46efab054e4a"
    dataset_id: str = "4570cf7b-a48f-440e-8f93-226828a3a243"
    report_id: str = "2f8ea0ef-30a2-442c-af53-b3fc7bfa1027"
    model_id: int = 11453601
    timeout: int = 30


@dataclass(frozen=True)
class VisualIDs:
    estado: str = "1939653a9d6bbd4abe2b"
    saldo: str = "fa2a9da34ca3522cc3b6"
    nombre: str = "a75cdb19088461402488"
    cta_contrato: str = "c034bb0d649b01c765c0"
    nse: str = "3ad014bf316f57fe6b8f"
    direccion: str = "04df67600e7aad10d3a0"
    distrito: str = "7f69ea308db71aa50aa7"
    documento: str = "123456789abc0def"
    estado_cta: str = "fedcba9876543210abcd"


CONFIG = PowerBIConfig()
VISUAL_IDS = VisualIDs()

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Content-Type": "application/json;charset=UTF-8",
    "Origin": "https://app.powerbi.com",
    "Referer": "https://app.powerbi.com/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-PowerBI-ResourceKey": CONFIG.resource_key,
}


def query_credit_line(dni: str) -> tuple[Optional[dict], str, Optional[str]]:
    estado = _query_field(dni, "Estado", VISUAL_IDS.estado)

    if not estado or estado == "--" or not estado.strip():
        return None, "not_found", "Client not found in GASO"

    name = _query_field(dni, "Cliente", VISUAL_IDS.nombre)
    balance = _query_field(dni, "Saldo", VISUAL_IDS.saldo)
    account = _query_field(dni, "Cuenta_contrato", VISUAL_IDS.cta_contrato)
    address = _query_field(dni, "Dirección", VISUAL_IDS.direccion)
    district = _query_field(dni, "Distrito", VISUAL_IDS.distrito)

    balance_amount = _parse_balance(balance)
    has_credit = balance_amount > 0 and estado.upper() != "NO APLICA"

    full_address = None
    if address and district:
        full_address = f"{address} - {district}"
    elif address:
        full_address = address
    elif district:
        full_address = district

    client_data = {
        "dni": dni,
        "nombre": name or "Cliente GASO",
        "estado": estado,
        "saldo": balance or "0",
        "cuentaContrato": account,
        "direccion": full_address,
        "tieneLineaCredito": has_credit,
        "lineaCredito": balance_amount,
        "segmento": "gaso",
    }

    return client_data, "success", None


def check_connection() -> bool:
    try:
        payload = _build_query_payload("00000000", "Estado", VISUAL_IDS.estado)
        response = _execute_query(payload)
        return response is not None
    except Exception:
        return False


def _query_field(dni: str, field_name: str, visual_id: str) -> Optional[str]:
    payload = _build_query_payload(dni, field_name, visual_id)
    response = _execute_query(payload)

    if not response:
        return None

    return _extract_value(response)


def _parse_balance(balance_str: str) -> float:
    if not balance_str:
        return 0.0

    try:
        clean = balance_str.replace("S/", "").strip()

        if not clean:
            return 0.0

        if "." in clean and "," in clean:
            clean = clean.replace(".", "").replace(",", ".")
        elif "," in clean and "." not in clean:
            clean = clean.replace(",", ".")
        elif "." in clean:
            parts = clean.split(".")
            if len(parts) == 2 and len(parts[1]) > 2:
                clean = clean.replace(".", "")

        return float(clean)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse balance: '{balance_str}'")
        return 0.0


def _build_query_payload(dni: str, property_name: str, visual_id: str) -> dict:
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


def _execute_query(payload: dict) -> Optional[dict]:
    try:
        url = f"{CONFIG.api_url}?synchronous=true"
        response = requests.post(
            url,
            headers=HEADERS,
            json=payload,
            timeout=CONFIG.timeout,
        )

        if response.status_code == 200:
            return response.json()

        logger.error(f"PowerBI API error: HTTP {response.status_code}")
        return None

    except requests.exceptions.Timeout:
        logger.error(f"PowerBI timeout ({CONFIG.timeout}s)")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"PowerBI connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"PowerBI query exception: {e}")
        return None


def _extract_value(response: dict) -> Optional[str]:
    try:
        results = response.get("results", [])
        if not results:
            return None

        result = results[0].get("result", {})
        data = result.get("data", {})
        dsr = data.get("dsr", {})
        ds = dsr.get("DS", [])

        if not ds:
            return None

        ph = ds[0].get("PH", [])
        if not ph:
            return None

        dm0 = ph[0].get("DM0", [])
        if not dm0:
            return None

        value = dm0[0].get("M0")
        if value is not None:
            return str(value).strip() or None

        return None
    except Exception as e:
        logger.error(f"Error extracting PowerBI value: {e}")
        return None
