#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")

from src.api.gaso_client import (
    _build_column_query_payload,
    _execute_query,
    _extract_column_value,
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
    # Mostrar estructura
    ds = response["results"][0]["result"]["data"]["dsr"]["DS"][0]

    print(f"\nDS keys: {list(ds.keys())}")

    if "ValueDicts" in ds:
        vd = ds["ValueDicts"]
        print(f"ValueDicts keys: {list(vd.keys())}")
        if "D0" in vd:
            print(f'ValueDicts.D0: {vd["D0"]}')

    if "PH" in ds:
        ph = ds["PH"][0]["DM0"]
        print(f"\nPH[0].DM0[0]: {ph[0]}")

    print("\n" + "=" * 70)
    valor = _extract_column_value(response)
    print(f"VALOR EXTRAIDO: {valor}")
else:
    print("SIN RESPUESTA DE POWER BI")
