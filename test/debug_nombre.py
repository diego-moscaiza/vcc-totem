#!/usr/bin/env python3
"""
Debug script para inspeccionar la respuesta exacta de Power BI para el campo Nombre
"""

import sys
import json
from pathlib import Path

# Configurar paths
ROOT = Path(__file__).parent
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

from src.api.gaso_client import (
    _build_query_payload,
    _execute_query,
    VISUAL_IDS,
    CONFIG,
)


def debug_nombre():
    """Consultar Nombre y mostrar la estructura completa de la respuesta"""
    dni = "44076453"

    print(f"\n{'=' * 70}")
    print(f"DEBUG: Consultando Nombre para DNI {dni}")
    print(f"{'=' * 70}\n")

    try:
        payload = _build_query_payload(dni, "Nombre", VISUAL_IDS.nombre)
        print("PAYLOAD:")
        print(json.dumps(payload, indent=2, ensure_ascii=False)[:500])
        print("...\n")

        response = _execute_query(payload, timeout=30)

        if response:
            print("RESPUESTA COMPLETA (formateada):")
            print(json.dumps(response, indent=2, ensure_ascii=False))

            # Análisis
            print(f"\n{'=' * 70}")
            print("ANÁLISIS DE ESTRUCTURA:")
            print(f"{'=' * 70}\n")

            results = response.get("results", [])
            if results:
                result = results[0].get("result", {})
                data = result.get("data", {})
                dsr = data.get("dsr", {})
                ds = dsr.get("DS", [])

                if ds:
                    first_ds = ds[0]
                    print(f"first_ds keys: {list(first_ds.keys())}")

                    # Mostrar estructura PH
                    ph = first_ds.get("PH", [])
                    if ph:
                        print(f"PH length: {len(ph)}")
                        for i, p in enumerate(ph):
                            print(f"  PH[{i}] keys: {list(p.keys())}")
                            if "DM0" in p:
                                dm0 = p.get("DM0", [])
                                print(f"    DM0 length: {len(dm0)}")
                                for j, d in enumerate(dm0):
                                    print(f"      DM0[{j}] keys: {list(d.keys())}")
                                    # Mostrar primeros valores
                                    for key in d.keys():
                                        val = d[key]
                                        if isinstance(val, (str, int, float)):
                                            print(f"        {key}: {val}")
                                        elif isinstance(val, list) and len(val) > 0:
                                            print(
                                                f"        {key}: [lista con {len(val)} elementos]"
                                            )
                                            if len(val) <= 3:
                                                print(f"          Contenido: {val}")

                    # Mostrar ValueDicts
                    value_dicts = first_ds.get("ValueDicts", {})
                    if value_dicts:
                        print(f"\nValueDicts keys: {list(value_dicts.keys())}")
                        for key, vals in value_dicts.items():
                            print(
                                f"  {key}: {vals if isinstance(vals, list) else type(vals)}"
                            )
        else:
            print("❌ No hay respuesta de Power BI")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    debug_nombre()
