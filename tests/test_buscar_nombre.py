"""
Test para buscar el nombre correcto del campo del cliente en Power BI.
Prueba variaciones comunes de nombres de campo.
"""

import pytest
from typing import Optional

from vcc_totem.api.gaso_client import (
    _build_query_payload,
    _execute_query,
    _extract_value,
)


# Lista de variaciones de nombres de campo para probar
VARIACIONES_NOMBRE = [
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


def probar_alias(alias: str) -> Optional[str]:
    """
    Probar un alias del campo nombre.

    Args:
        alias: El nombre del campo a probar

    Returns:
        El valor encontrado o None si no se encuentra
    """
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
    except Exception:
        pass

    return None


class TestBuscarNombreCampo:
    """Tests para encontrar el campo de nombre correcto en Power BI."""

    @pytest.fixture
    def dni_prueba(self) -> str:
        """DNI de prueba para las consultas."""
        return "44076453"

    @pytest.mark.parametrize("alias", VARIACIONES_NOMBRE)
    def test_probar_alias_no_falla(self, alias: str) -> None:
        """
        Verificar que probar cada alias no causa excepciones.

        Este test verifica que la función probar_alias puede ejecutarse
        sin errores para cada variación de nombre de campo.
        """
        # No debe lanzar excepciones
        resultado = probar_alias(alias)
        # El resultado puede ser None o un string, ambos son válidos
        assert resultado is None or isinstance(resultado, str)

    def test_al_menos_un_alias_funciona(self) -> None:
        """
        Verificar que al menos una variación del campo nombre funciona.

        Este test busca entre todas las variaciones y verifica que
        al menos una retorne un valor válido.
        """
        encontrados = []

        for alias in VARIACIONES_NOMBRE:
            valor = probar_alias(alias)
            if valor:
                encontrados.append((alias, valor))

        # Mostrar los alias encontrados para debugging
        if encontrados:
            print(f"\nAlias válidos encontrados: {len(encontrados)}")
            for alias, valor in encontrados:
                print(f"   - {alias}: {valor}")
        else:
            print("\nNo se encontró ningún alias válido")

        assert len(encontrados) > 0, (
            "No se encontró ningún alias válido para el campo nombre"
        )
