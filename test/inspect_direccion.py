#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")

from src.api.gaso_client import (
    _build_query_payload,
    _execute_query,
    VISUAL_IDS,
)
import json

dni = "44076453"

print(f'Inspeccionando respuesta de "Dirección"')
print("=" * 70)

payload = _build_query_payload(dni, "Dirección", VISUAL_IDS.nombre)
response = _execute_query(payload, timeout=5)

print(json.dumps(response, indent=2, default=str)[:3000])
