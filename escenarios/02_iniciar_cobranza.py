"""
Escenario 2 — Iniciar cobranza.

En el sistema de Somos Rentable, esto se llama automáticamente cuando
una cuota vence y el cliente no pagó. Lo dispara un cron job, un trigger
de base de datos, o un worker — lo que sea que ya tengan.

No es una acción manual. El dev lo integra una vez y después funciona solo.

Correr:
    python3 escenarios/02_iniciar_cobranza.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from kobra import KobraClient, CobranzaYaActiva, KobraError

load_dotenv()

# -----------------------------------------------------------------------
# Esto simula un deudor que existe en el sistema de Somos Rentable.
# En producción, estos datos vendrían de su base de datos.
# -----------------------------------------------------------------------
DEUDOR_EJEMPLO = {
    "deudor_id": "SR-12345",           # ID interno de Somos Rentable
    "nombre":    "Juan Pérez",
    "telefono":  "+56912345678",       # número real o de prueba
    "monto":     150000,               # pesos chilenos
    "concepto":  "Cuota octubre 2026 — Proyecto Bello Horizonte Depto 304",
}


async def main():
    kobra = KobraClient(
        api_key=os.environ["KOBRA_API_KEY"],
        base_url=os.environ.get("KOBRA_BASE_URL"),
    )

    print(f"\n{'='*50}")
    print("Iniciando cobranza...")
    print(f"{'='*50}")
    print(f"  Deudor:  {DEUDOR_EJEMPLO['nombre']}")
    print(f"  Monto:   ${DEUDOR_EJEMPLO['monto']:,.0f}".replace(",", "."))
    print(f"  Concepto: {DEUDOR_EJEMPLO['concepto']}")
    print(f"  Teléfono: {DEUDOR_EJEMPLO['telefono']}")
    print()

    try:
        resultado = await kobra.iniciar_cobranza(**DEUDOR_EJEMPLO)

        print(f"✓ Cobranza iniciada")
        print(f"\n  conversation_id: {resultado['conversation_id']}")
        print(f"  (Guardalo si querés rastrear este caso)")
        print(f"\n  Primer mensaje que Carolina le envió al deudor:")
        print(f"  ┌─────────────────────────────────────────────┐")
        for linea in (resultado.get("primer_mensaje") or "").split("\n"):
            print(f"  │ {linea}")
        print(f"  └─────────────────────────────────────────────┘")
        print(f"\n  Carolina va a negociar sola a partir de acá.")
        print(f"  Cuando el deudor pague, Kobra te avisa por webhook.")

    except CobranzaYaActiva as e:
        print(f"[!] Ya existe una cobranza activa para este número.")
        print(f"    {e.detail}")
        print(f"    Podés rastrear el caso con el conversation_id anterior.")

    except KobraError as e:
        print(f"✗ Error de Kobra ({e.status_code}): {e.detail}")

    except Exception as e:
        print(f"✗ Error inesperado: {e}")


asyncio.run(main())
