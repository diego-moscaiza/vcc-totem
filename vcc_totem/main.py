"""
Usa este comando para buscar por DNI:
uv run vcc_totem/main.py -- 12345678        (equivalente a python run vcc_totem/main.py 12345678)

Si deseas una respuesta en formato JSON, agrega --json:
uv run vcc_totem/main.py -- 12345678 --json

O solo ejecútalo para usar el modo interactivo:
uv run vcc_totem/main.py
"""

import logging
from pathlib import Path

import click

from vcc_totem.config import LOG_FILE, LOG_LEVEL
from vcc_totem.core.query import query_with_fallback, validate_dni
from vcc_totem.core.messages import format_response

log_path = Path(__file__).parent / LOG_FILE
log_path.parent.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


@click.command()
@click.argument("dni", required=False)
@click.option("--json", is_flag=True, help="Salida en formato JSON")
def main(dni, json):
    # Single query mode
    if dni:
        query_dni(dni, json)
        return

    # Interactive mode
    click.echo("Ingrese DNI (o 'q' para salir)\n")
    while True:
        dni = click.prompt("DNI", type=str).strip()
        if dni.lower() == "q":
            break
        query_dni(dni, json)
        click.echo()


def query_dni(dni, as_json):
    """Query a single DNI."""
    try:
        dni = validate_dni(dni)
    except ValueError as e:
        click.secho(f"DNI inválido: {e}", fg="red", err=True)
        return

    result = query_with_fallback(dni)
    message, has_offer = format_response(result)

    if as_json:
        import json

        response = {
            "success": result.success,
            "dni": result.dni,
            "channel": result.channel,
            "has_offer": result.has_offer,
        }
        if result.data:
            response["data"] = result.data
        if result.error_message:
            response["error"] = result.error_message

        click.echo(json.dumps(response, indent=2))
    else:
        click.echo(f"\n{message}")
        color = "green" if has_offer else "yellow"
        click.secho(f"Oferta: {'Sí' if has_offer else 'No'}\n", fg=color)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        click.echo("\n")
