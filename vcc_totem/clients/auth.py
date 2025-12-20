import jwt
import requests
import logging

from vcc_totem.config import USUARIO, PASSWORD, LOGIN_API, TIMEOUT

logger = logging.getLogger(__name__)


def login():
    session = requests.Session()
    session.headers.update(
        {
            "accept": "application/json, text/plain, */*",
            "accept-language": "es-419,es;q=0.9",
            "content-type": "application/json",
            "origin": "https://appweb.calidda.com.pe",
            "referer": "https://appweb.calidda.com.pe/WebFNB/login",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
    )

    payload = {
        "usuario": USUARIO,
        "password": PASSWORD,
        "captcha": "exitoso",
        "Latitud": "",
        "Longitud": "",
    }

    try:
        response = session.post(LOGIN_API, json=payload, timeout=TIMEOUT)

        if response.status_code != 200:
            logger.error(f"Login failed: HTTP {response.status_code}")
            return None, None

        data = response.json()

        if not data.get("valid"):
            logger.error(f"Login invalid: {data.get('message')}")
            return None, None

        auth_data = data.get("data", {})
        token = auth_data.get("authToken")

        if not token:
            logger.error("No authToken in response")
            return None, None

        decoded = jwt.decode(token, options={"verify_signature": False})
        ally_id = decoded.get("commercialAllyId")

        session.headers.update(
            {
                "authorization": f"Bearer {token}",
                "referer": "https://appweb.calidda.com.pe/WebFNB/consulta-credito",
            }
        )

        return session, ally_id

    except Exception as e:
        logger.error(f"Login exception: {e}")
        return None, None
