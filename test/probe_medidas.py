#!/usr/bin/env python3
import sys

sys.path.insert(0, "src")

from src.api.gaso_client import (
    _build_query_payload,
    _execute_query,
    _extract_value,
    VISUAL_IDS,
)

dni = "44076453"

# Probar diferentes nombres de MEDIDAS
medidas_a_probar = [
    "Nombre",
    "nombre",
    "NOMBRE",
    "Dirección",
    "direccion",
    "Distrito",
    "distrito",
    "Estado",
    "estado",
    "Saldo",
    "saldo",
    "Cuenta_contrato",
    "Cuenta Contrato",
    "cuenta_contrato",
    "NSE",
    "nse",
]

print(f"Probando MEDIDAS con DNI {dni}")
print("=" * 70)

for medida in medidas_a_probar:
    print(f"\nMedida: {medida}...", end=" ")
    try:
        payload = _build_query_payload(dni, medida, VISUAL_IDS.nombre)
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
                        msg = (
                            shape["odata.error"]
                            .get("message", {})
                            .get("value", "ERROR")
                        )
                        if "Could not resolve" in msg:
                            print(f"❌ Columna/Medida no existe")
                        else:
                            print(f"❌ ERROR: {msg[:50]}")
                        continue
                    elif "DS" in dsr and dsr["DS"]:
                        # Éxito
                        valor = _extract_value(response)
                        print(f"✓ VALOR: {valor}")
                        continue

        print(f"? Sin respuesta válida")
    except Exception as e:
        print(f"❌ EXCEPCION: {str(e)[:30]}")

print("\n" + "=" * 70)
