import time
import threading
import logging
import requests
from typing import Tuple

from vcc_totem.clients.auth import login

logger = logging.getLogger(__name__)

SESSION_TTL = 3600
_cache = {"session": None, "ally_id": None, "timestamp": 0}
_lock = threading.Lock()


def get_session(force_refresh: bool = False) -> Tuple[requests.Session, str]:
    now = time.time()

    if not force_refresh and _cache["session"]:
        age = now - _cache["timestamp"]
        if age < SESSION_TTL:
            return _cache["session"], _cache["ally_id"]

    with _lock:
        if not force_refresh and _cache["session"]:
            age = time.time() - _cache["timestamp"]
            if age < SESSION_TTL:
                return _cache["session"], _cache["ally_id"]

        session, ally_id = login()

        if not session:
            raise RuntimeError("Failed to authenticate with FNB")

        _cache["session"] = session
        _cache["ally_id"] = ally_id
        _cache["timestamp"] = time.time()

        return session, ally_id


def invalidate_session() -> None:
    _cache["timestamp"] = 0
