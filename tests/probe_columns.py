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

dni = "44076453"

# Probar diferentes nombres de columnas
nombres_a_probar = [
    "Nombre",
    "nombre",
    "NOMBRE",
    "NombreCliente",
    "nombre_cliente",
    "Nombre Cliente",
    "Cliente",
    "cliente",
    "CLIENTE",
    "ClienteName",
    "Nombre_Cliente",
    "full_name",
    "FullName",
    "Desc_Cliente",
    "Descripcion",
]

for col_name in nombres_a_probar:
    print(f"\nProbando: {col_name}...", end=" ")
    try:
        payload = _build_column_query_payload(dni, col_name, VISUAL_IDS.nombre)
        response = _execute_query(payload, timeout=5)

        if response and "results" in response and response["results"]:
            result = response["results"][0].get("result", {})
            data = result.get("data", {})

            # Verificar si hay error
            if "dsr" in data:
                dsr = data["dsr"]
                if "DataShapes" in dsr and dsr["DataShapes"]:
                    shape = dsr["DataShapes"][0]
                    if "odata.error" in shape:
                        print(f"❌ ERROR")
                        continue
                    elif "DS" in dsr:
                        # Éxito
                        valor = _extract_column_value(response)
                        print(f"✓ VALOR: {valor}")
                        continue

        print(f"? Sin respuesta válida")
    except Exception as e:
        print(f"❌ EXCEPCION")

print("\n" + "=" * 70)
print("Intenta verificar en el dashboard de Power BI el nombre exacto del campo")
