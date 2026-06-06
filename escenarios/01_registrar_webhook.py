"""
Escenario 1 — Registrar webhook.

La primera vez que configurás la integración, le decís a Kobra a dónde
avisarte cuando pase algo.

Esto se hace una sola vez. En producción, ponés la URL de tu sistema real.
Para desarrollo local, necesitás una URL pública (ngrok, etc.).

Correr:
    python3 escenarios/01_registrar_webhook.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from kobra import KobraClient

load_dotenv()


def main():
    kobra = KobraClient(
        api_key=os.environ["KOBRA_API_KEY"],
        base_url=os.environ.get("KOBRA_BASE_URL"),
    )

    # -----------------------------------------------------------------------
    # En producción: usás la URL pública de tu sistema.
    # Para desarrollo: levantás servidor_webhooks.py y usás ngrok.
    #
    # Ejemplo con ngrok:
    #   ngrok http 8000
    #   → te da una URL como https://abc123.ngrok.io
    #   → la pegás acá abajo
    # -----------------------------------------------------------------------

    webhook_url = input(
        "\n¿Cuál es la URL pública de tu receptor de webhooks?\n"
        "(Ej: https://api.somosrentable.cl/webhooks/kobra\n"
        "     https://abc123.ngrok.io/webhooks/kobra)\n\n"
        "URL: "
    ).strip()

    if not webhook_url:
        print("[!] No ingresaste una URL. Abortando.")
        return

    print(f"\nRegistrando webhook: {webhook_url}")
    print("Eventos suscriptos: cobrado, acuerdo")
    print("...")

    try:
        resultado = kobra.registrar_webhook(
            url=webhook_url,
            eventos=["cobrado", "acuerdo"],
        )
        print(f"\n✓ Webhook registrado exitosamente")
        print(f"  URL:     {resultado.url}")
        print(f"  Eventos: {', '.join(resultado.eventos)}")
        print(f"\nDesde ahora, Kobra te avisará automáticamente cuando:")
        print(f"  - Un deudor pague              → evento 'cobrado'")
        print(f"  - Un deudor prometa pagar      → evento 'acuerdo'")
    except Exception as e:
        print(f"\n✗ Error: {e}")


main()
