#!/usr/bin/env python3
"""
Buscar el nombre correcto del campo del cliente en Power BI
Probar variaciones comunes
"""

import sys
from pathlib import Path

# Configurar paths
ROOT = Path(__file__).parent
SRC = ROOT / "src"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))

from src.api.gaso_client import (
    _build_query_payload,
    _execute_query,
    _extract_value,
)


def probar_alias(alias):
    """Probar un alias del campo nombre"""
    dni = "44076453"

    try:
        payload = _build_query_payload(dni, alias, "test-visual-id")
        response = _execute_query(payload, timeout=30)

        if response and "results" in response and response["results"]:
            result = response["results"][0].get("result", {})
            data = result.get("data", {})
            dsr = data.get("dsr", {})

            # Verificar si hay error
            if "DataShapes" in dsr:
                shapes = dsr.get("DataShapes", [])
                if shapes and "odata.error" in shapes[0]:
                    return None

            # Intentar extraer valor
            valor = _extract_value(response)
            return valor
    except:
        pass

    return None


if __name__ == "__main__":
    # Variaciones comunes del campo nombre
    variaciones = [
        "Nombre",
        "nombre",
        "Cliente",
        "cliente",
        "Nombre_Cliente",
        "NombreCliente",
        "Nombre Cliente",
        "ClienteName",
        "FullName",
        "Razón Social",
        "Razon Social",
        "Denominación",
        "Denominacion",
        "Cliente_Nombre",
        "CLIENTE",
        "NOMBRE",
        "Name",
        "Titular",
        "Persona",
        "Denominación Legal",
        "Denominacion Legal",
    ]

    print("\n" + "=" * 60)
    print("BUSCANDO NOMBRE CORRECTO DEL CAMPO CLIENTE")
    print("=" * 60 + "\n")

    encontrados = []

    for alias in variaciones:
        valor = probar_alias(alias)
        if valor:
            print(f"✅ ENCONTRADO: '{alias}' = {valor}")
            encontrados.append((alias, valor))
        else:
            print(f"❌ {alias}")

    print("\n" + "=" * 60)
    if encontrados:
        print(f"RESULTADO: Se encontraron {len(encontrados)} alias válidos:")
        for alias, valor in encontrados:
            print(f"  - {alias}: {valor}")
    else:
        print("RESULTADO: No se encontró un alias válido para el campo nombre")
    print("=" * 60)
