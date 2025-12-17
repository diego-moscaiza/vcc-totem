import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
env_path = ROOT_DIR / ".env"

load_dotenv(dotenv_path=env_path)

if not env_path.exists():
    raise FileNotFoundError(
        f"File .env not found at {env_path}. Copy .env.example to .env"
    )

USUARIO = os.getenv("CALIDDA_USUARIO")
PASSWORD = os.getenv("CALIDDA_PASSWORD")

if not USUARIO or not PASSWORD:
    raise ValueError("CALIDDA_USUARIO and CALIDDA_PASSWORD must be set in .env")

BASE_URL = os.getenv("BASE_URL", "https://appweb.calidda.com.pe")
LOGIN_API = BASE_URL + os.getenv("LOGIN_API", "/FNB_Services/api/Seguridad/autenticar")
CONSULTA_API = BASE_URL + os.getenv(
    "CONSULTA_API", "/FNB_Services/api/financiamiento/lineaCredito"
)

DELAY_MIN = float(os.getenv("DELAY_MIN", "10"))
DELAY_MAX = float(os.getenv("DELAY_MAX", "207"))
TIMEOUT = int(os.getenv("TIMEOUT", "300"))
MAX_CONSULTAS_POR_SESION = int(os.getenv("MAX_CONSULTAS_POR_SESION", "50"))

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "consultas_credito")
DNIS_FILE = os.getenv("DNIS_FILE", "lista_dnis.txt")

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/extractor.log")

(ROOT_DIR / "logs").mkdir(exist_ok=True)
