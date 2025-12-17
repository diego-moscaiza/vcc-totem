import requests
import logging
from typing import Optional

from vcc_totem.config import CONSULTA_API, TIMEOUT

logger = logging.getLogger(__name__)


def query_credit_line(
    session: requests.Session, dni: str, ally_id: str
) -> tuple[Optional[dict], str, Optional[str]]:
    params = {
        "numeroDocumento": dni,
        "tipoDocumento": "PE2",
        "idAliado": ally_id,
        "canal": "FNB",
    }

    try:
        response = session.get(CONSULTA_API, params=params, timeout=TIMEOUT)

        if response.status_code == 200:
            data = response.json()

            if data is None:
                logger.error(f"Empty response for DNI {dni}")
                return None, "error", "Empty response from API"

            if data.get("valid"):
                if "data" not in data:
                    logger.error(f"Missing data field for DNI {dni}")
                    return None, "error", "Missing data field in response"

                client_data = data["data"]
                client_data["segmento"] = "fnb"
                return client_data, "success", None

            message = data.get("message", "No message provided")
            return None, "not_found", message

        if response.status_code == 401:
            return None, "session_expired", "Session expired"

        if response.status_code == 429:
            return None, "rate_limited", "Too many requests"

        logger.error(f"FNB API error: HTTP {response.status_code}")
        return None, "error", f"HTTP {response.status_code}"

    except requests.exceptions.Timeout:
        logger.error(f"Timeout querying DNI {dni} after {TIMEOUT}s")
        return None, "timeout", f"Request timeout after {TIMEOUT} seconds"

    except Exception as e:
        logger.error(f"FNB query exception for DNI {dni}: {e}")
        return None, "error", str(e)
