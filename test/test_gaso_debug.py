#!/usr/bin/env python3
"""
Script de debugging para entender qué está pasando con GASO
"""

import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "src"))

import logging

logging.basicConfig(
    level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s"
)

from src.api.gaso_client import (
    _build_column_query_payload,
    _execute_query,
    _extract_column_value,
    _build_query_payload,
    _extract_value,
    VISUAL_IDS,
)


def test_nombre(dni: str = "44076451"):
    """Probar extracción del nombre"""
    print(f"\n{'=' * 70}")
    print(f"PROBANDO NOMBRE PARA DNI: {dni}")
    print(f"{'=' * 70}")

    # Construcción de payload para columna
    print(f"\n1. Construyendo payload para Nombre (como COLUMNA)...")
    payload = _build_column_query_payload(dni, "Nombre", VISUAL_IDS.nombre)
    print(f"   Visual ID: {VISUAL_IDS.nombre}")
    print(
        f"   Query From: {[f['Entity'] for f in payload['queries'][0]['Query']['Commands'][0]['SemanticQueryDataShapeCommand']['Query']['From']]}"
    )
    print(
        f"   Select: {[s['Column']['Property'] for s in payload['queries'][0]['Query']['Commands'][0]['SemanticQueryDataShapeCommand']['Query']['Select']]}"
    )

    # Ejecutar query
    print(f"\n2. Ejecutando query...")
    response = _execute_query(payload, timeout=10)

    if not response:
        print("   ❌ SIN RESPUESTA DE POWER BI")
        return

    print(f"   ✓ Respuesta recibida")

    # Mostrar estructura de respuesta completa
    print(f"\n3. Estructura completa de respuesta:")
    import json

    print(json.dumps(response, indent=2, default=str)[:2000])

    # Extraer valor
    print(f"\n4. Extrayendo valor con DEBUG...")
    valor = _extract_column_value(response)
    print(f"   Valor extraído: '{valor}'")

    return valor


def test_saldo(dni: str = "44076451"):
    """Probar extracción del saldo"""
    print(f"\n{'=' * 70}")
    print(f"PROBANDO SALDO PARA DNI: {dni}")
    print(f"{'=' * 70}")

    # Construcción de payload para medida
    print(f"\n1. Construyendo payload para Saldo (como MEDIDA)...")
    payload = _build_query_payload(dni, "Saldo", VISUAL_IDS.saldo)
    print(f"   Visual ID: {VISUAL_IDS.saldo}")
    print(
        f"   Query From: {[f['Entity'] for f in payload['queries'][0]['Query']['Commands'][0]['SemanticQueryDataShapeCommand']['Query']['From']]}"
    )

    # Ejecutar query
    print(f"\n2. Ejecutando query...")
    response = _execute_query(payload, timeout=10)

    if not response:
        print("   ❌ SIN RESPUESTA DE POWER BI")
        return

    print(f"   ✓ Respuesta recibida")

    # Extraer valor
    print(f"\n3. Extrayendo valor...")
    valor = _extract_value(response)
    print(f"   Valor extraído: '{valor}'")

    return valor


if __name__ == "__main__":
    dni = "44076451"

    # Probar saldo primero (medida, que funciona)
    saldo = test_saldo(dni)

    # Luego probar nombre (columna, que no funciona)
    nombre = test_nombre(dni)

    print(f"\n{'=' * 70}")
    print(f"RESUMEN:")
    print(f"{'=' * 70}")
    print(f"DNI: {dni}")
    print(f"Saldo: {saldo}")
    print(f"Nombre: {nombre}")
