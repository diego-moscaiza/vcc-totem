#!/usr/bin/env python3
"""
Script simple de debugging sin iniciar servidor
"""

import sys
from pathlib import Path

# Agregar src al path
root_dir = Path(__file__).parent
sys.path.insert(0, str(root_dir / "src"))

import logging

logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(message)s")

from src.api.gaso_client import (
    _build_column_query_payload,
    _build_query_payload,
    _execute_query,
    _extract_column_value,
    _extract_value,
    VISUAL_IDS,
    consultar_dni_gaso,
)

dni = "44076451"

print("\n" + "=" * 80)
print(f"CONSULTANDO DNI: {dni}")
print("=" * 80)

# Llamar a la función principal
datos, estado, error = consultar_dni_gaso(dni)

print(f"\n{'='*80}")
print(f"RESULTADO:")
print(f"{'='*80}")
print(f"Estado: {estado}")
print(f"Error: {error}")
if datos:
    print(f"\nDatos obtenidos:")
    for clave, valor in datos.items():
        print(f"  - {clave}: {valor}")
else:
    print("NO SE OBTUVIERON DATOS")
