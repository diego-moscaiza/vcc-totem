#!/usr/bin/env python3
"""
Script de prueba para verificar que las respuestas incluyen 'segmento'
Prueba ambos segmentos: FNB y GASO
"""

import sys
from pathlib import Path
import json

# Agregar rutas correctas
root_dir = Path(__file__).parent.parent
src_dir = root_dir / "src"
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(src_dir))

from config import mostrar_config
from api.auth import login
from api.client import consultar_dni
from api.gaso_client import consultar_dni_gaso


def prueba_fnb():
    """Prueba consulta FNB con segmento"""
    print("\n" + "=" * 80)
    print("🧪 PRUEBA FNB - Verificar clave 'segmento'")
    print("=" * 80)

    try:
        # Login en FNB
        session, id_aliado = login()

        if not session:
            print("❌ Error: No se pudo iniciar sesión en FNB")
            return False

        print("✅ Sesión FNB iniciada")

        # Solicitar DNI para prueba
        dni = input(
            "\nIngresa un DNI para probar FNB (o presiona Enter para saltar): "
        ).strip()

        if not dni:
            print("⏭️  Prueba FNB saltada")
            return True

        if not dni.isdigit() or len(dni) != 8:
            print("❌ DNI inválido")
            return False

        print(f"\nConsultando DNI: {dni}")
        data, estado, mensaje = consultar_dni(session, dni, id_aliado)

        if data and data.get("id"):
            print("\n✅ Respuesta recibida:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if "segmento" in data:
                if data["segmento"] == "fnb":
                    print(
                        "\n✅ ¡CORRECTO! La clave 'segmento' está presente con valor 'fnb'"
                    )
                    return True
                else:
                    print(
                        f"\n❌ Error: El valor de 'segmento' es '{data['segmento']}' en lugar de 'fnb'"
                    )
                    return False
            else:
                print("\n❌ Error: La clave 'segmento' NO está en la respuesta")
                return False
        else:
            print(f"⚠️  DNI no válido o sin oferta: {estado}")
            return True

    except Exception as e:
        print(f"❌ Error en prueba FNB: {e}")
        import traceback

        traceback.print_exc()
        return False


def prueba_gaso():
    """Prueba consulta GASO con segmento"""
    print("\n" + "=" * 80)
    print("🧪 PRUEBA GASO - Verificar clave 'segmento'")
    print("=" * 80)

    try:
        # Solicitar DNI para prueba
        dni = input(
            "\nIngresa un DNI para probar GASO (o presiona Enter para saltar): "
        ).strip()

        if not dni:
            print("⏭️  Prueba GASO saltada")
            return True

        if not dni.isdigit() or len(dni) != 8:
            print("❌ DNI inválido")
            return False

        print(f"\nConsultando DNI en GASO: {dni}")
        data, estado, mensaje = consultar_dni_gaso(dni)

        if data and estado == "success":
            print("\n✅ Respuesta recibida:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            if "segmento" in data:
                if data["segmento"] == "gaso":
                    print(
                        "\n✅ ¡CORRECTO! La clave 'segmento' está presente con valor 'gaso'"
                    )
                    return True
                else:
                    print(
                        f"\n❌ Error: El valor de 'segmento' es '{data['segmento']}' en lugar de 'gaso'"
                    )
                    return False
            else:
                print("\n❌ Error: La clave 'segmento' NO está en la respuesta")
                return False
        else:
            print(f"⚠️  DNI no encontrado en GASO: {estado}")
            return True

    except Exception as e:
        print(f"❌ Error en prueba GASO: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Función principal"""
    print("\n")
    print("🚀 PRUEBA DE RESPUESTAS CON CLAVE 'SEGMENTO'")
    print("=" * 80)

    # Mostrar configuración
    mostrar_config()

    # Ejecutar pruebas
    resultado_fnb = prueba_fnb()
    resultado_gaso = prueba_gaso()

    # Resumen
    print("\n" + "=" * 80)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 80)
    print(f"FNB:  {'✅ PASÓ' if resultado_fnb else '❌ FALLÓ'}")
    print(f"GASO: {'✅ PASÓ' if resultado_gaso else '❌ FALLÓ'}")

    if resultado_fnb and resultado_gaso:
        print("\n✅ ¡TODAS LAS PRUEBAS PASARON!")
    else:
        print("\n⚠️  Algunas pruebas fallaron")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback

        traceback.print_exc()
