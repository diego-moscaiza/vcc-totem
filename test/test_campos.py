#!/usr/bin/env python3
"""
Probar cada campo para determinar si es Columna o Medida
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
    _build_column_query_payload,
    _execute_query,
    _extract_value,
    _extract_column_value,
    VISUAL_IDS,
)


def probar_campo(nombre_campo, es_columna=False):
    """Probar un campo específico"""
    dni = "44076453"

    print(f"\n{'=' * 60}")
    print(f"Probando: {nombre_campo} ({'COLUMNA' if es_columna else 'MEDIDA'})")
    print(f"{'=' * 60}")

    try:
        # Usar el payload apropiado
        if es_columna:
            payload = _build_column_query_payload(dni, nombre_campo, "test-visual-id")
        else:
            payload = _build_query_payload(dni, nombre_campo, "test-visual-id")

        response = _execute_query(payload, timeout=30)

        if response:
            # Verificar si hay error
            if "results" in response and response["results"]:
                result = response["results"][0].get("result", {})
                data = result.get("data", {})
                dsr = data.get("dsr", {})

                # Verificar si hay error en DataShapes
                if "DataShapes" in dsr:
                    shapes = dsr.get("DataShapes", [])
                    if shapes and "odata.error" in shapes[0]:
                        error_msg = shapes[0]["odata.error"].get("message", {})
                        if isinstance(error_msg, dict):
                            error_msg = error_msg.get("value", str(error_msg))
                        print(f"❌ ERROR: {error_msg}")
                        return False

                # Intentar extraer valor
                if es_columna:
                    valor = _extract_column_value(response)
                else:
                    valor = _extract_value(response)

                if valor:
                    print(f"✅ ÉXITO: Valor = {valor}")
                    return True
                else:
                    print(f"⚠️ Sin valor retornado")
                    return False
        else:
            print("❌ Sin respuesta de Power BI")
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False


if __name__ == "__main__":
    # Probar como MEDIDAS
    print("\n" + "=" * 60)
    print("PROBANDO COMO MEDIDAS")
    print("=" * 60)

    campos_medida = [
        "Estado",
        "Saldo",
        "Nombre",
        "Cuenta_contrato",
        "NSE",
        "Dirección",
        "Distrito",
        "Documento",
        "Estado_cta",
    ]
    medidas_resultado = {}

    for campo in campos_medida:
        resultado = probar_campo(campo, es_columna=False)
        medidas_resultado[campo] = resultado

    # Probar como COLUMNAS
    print("\n" + "=" * 60)
    print("PROBANDO COMO COLUMNAS")
    print("=" * 60)

    columnas_resultado = {}
    for campo in campos_medida:
        resultado = probar_campo(campo, es_columna=True)
        columnas_resultado[campo] = resultado

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)

    print("\nCOMO MEDIDAS:")
    for campo, resultado in medidas_resultado.items():
        status = "✅" if resultado else "❌"
        print(f"  {status} {campo}")

    print("\nCOMO COLUMNAS:")
    for campo, resultado in columnas_resultado.items():
        status = "✅" if resultado else "❌"
        print(f"  {status} {campo}")

    print("\nRECOMENDACIONES:")
    for campo in campos_medida:
        es_medida = medidas_resultado.get(campo, False)
        es_columna = columnas_resultado.get(campo, False)

        if es_medida:
            print(f"  {campo}: USAR _build_query_payload()")
        elif es_columna:
            print(f"  {campo}: USAR _build_column_query_payload()")
        else:
            print(f"  {campo}: ❌ NO FUNCIONA")
