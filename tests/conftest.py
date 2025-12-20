"""
Our strategy is:
- ONE real API call per DNI, cached in tests/.cache/
- Fetch once, test many times
- Use test_dnis.txt for maintainable list of edge cases
"""

import json
from pathlib import Path

import pytest

CACHE_DIR = Path(__file__).parent / ".cache"
DNIS_FILE = Path(__file__).parent / "test_dnis.txt"


def pytest_configure(config):
    """Create cache directory."""
    CACHE_DIR.mkdir(exist_ok=True)


def load_test_dnis():
    """Load DNIs from test_dnis.txt file."""
    dnis = []
    if DNIS_FILE.exists():
        for line in DNIS_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                parts = line.split(",", 1)
                dni = parts[0].strip()
                if dni:
                    dnis.append(dni)
    return dnis if dnis else ["44076453"]


def _cache_path(dni, channel):
    return CACHE_DIR / f"{channel}_{dni}.json"


def _load_cached(dni, channel):
    path = _cache_path(dni, channel)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None


def _save_cached(dni, channel, data):
    path = _cache_path(dni, channel)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_gaso(dni):
    """Fetch GASO response, cached."""
    cached = _load_cached(dni, "gaso")
    if cached:
        return cached

    from vcc_totem.clients.gaso import query_credit_line

    data, status, error = query_credit_line(dni)
    result = {"dni": dni, "data": data, "status": status, "error": error}
    _save_cached(dni, "gaso", result)
    return result


def fetch_fnb(dni):
    """Fetch FNB response, cached."""
    cached = _load_cached(dni, "fnb")
    if cached:
        return cached

    from vcc_totem.clients import fnb, session

    try:
        sess, ally_id = session.get_session()
        data, status, error = fnb.query_credit_line(sess, dni, ally_id)
    except Exception as e:
        data, status, error = None, "error", str(e)

    result = {"dni": dni, "data": data, "status": status, "error": error}
    _save_cached(dni, "fnb", result)
    return result


@pytest.fixture(scope="session")
def test_dnis():
    """All DNIs from test_dnis.txt."""
    return load_test_dnis()


@pytest.fixture(scope="session")
def gaso_responses(test_dnis):
    """All GASO responses for test DNIs, cached."""
    return {dni: fetch_gaso(dni) for dni in test_dnis}


@pytest.fixture(scope="session")
def fnb_responses(test_dnis):
    """All FNB responses for test DNIs, cached."""
    return {dni: fetch_fnb(dni) for dni in test_dnis}
