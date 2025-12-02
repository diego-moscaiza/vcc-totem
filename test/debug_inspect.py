#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")

from src.api.gaso_client import (
    _build_column_query_payload,
    _execute_query,
    VISUAL_IDS,
)
import json

dni = "44076451"
print(f"Probando Nombre para DNI {dni}")
print("=" * 70)

# Construir y ejecutar query
payload = _build_column_query_payload(dni, "Nombre", VISUAL_IDS.nombre)
response = _execute_query(payload, timeout=10)

if response:
    print("\nRESPUESTA COMPLETA:")
    print(json.dumps(response, indent=2, default=str)[:3000])
else:
    print("SIN RESPUESTA DE POWER BI")
