"""
Escenario 3 — Simular un evento entrante de Kobra.

Cuando trabajás en el servidor de webhooks, necesitás probarlo sin
esperar a que un deudor real pague. Este script manda un POST falso
a tu servidor local, como si fuera Kobra.

Usarlo junto con servidor_webhooks.py:

  Terminal 1:  python3 servidor_webhooks.py
  Terminal 2:  python3 escenarios/03_simular_evento.py

Correr:
    python3 escenarios/03_simular_evento.py
"""

import asyncio
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_LOCAL_URL = f"http://localhost:{os.environ.get('WEBHOOK_LOCAL_PORT', 8000)}/webhooks/kobra"

EVENTOS_EJEMPLO = {
    "cobrado": {
        "evento": "cobrado",
        "conversation_id": "a1b2c3d4",
        "deudor_id": "SR-12345",
        "monto": 150000,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    },
    "acuerdo": {
        "evento": "acuerdo",
        "conversation_id": "a1b2c3d4",
        "deudor_id": "SR-12345",
        "monto_acordado": 150000,
        "fecha_pago": "2026-06-15",
        "link_pago": "https://khipu.com/payment/demo-abc123",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    },
}


async def main():
    print(f"\nSimulador de eventos Kobra")
    print(f"Enviando evento a: {WEBHOOK_LOCAL_URL}")
    print()
    print(f"¿Qué evento querés simular?")
    print(f"  1. cobrado  — el deudor pagó")
    print(f"  2. acuerdo  — el deudor prometió pagar")
    opcion = input("\nElegí (1/2): ").strip()

    evento_key = "cobrado" if opcion == "1" else "acuerdo"
    payload = EVENTOS_EJEMPLO[evento_key]

    print(f"\nEnviando evento '{evento_key}'...")
    print(f"Payload: {payload}")
    print()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(WEBHOOK_LOCAL_URL, json=payload)
            if resp.status_code == 200:
                print(f"✓ Evento enviado. Tu servidor lo procesó.")
                print(f"  Mirá la terminal donde corre servidor_webhooks.py para ver el log.")
            else:
                print(f"✗ Tu servidor respondió {resp.status_code}: {resp.text}")
    except httpx.ConnectError:
        print(f"✗ No se pudo conectar a {WEBHOOK_LOCAL_URL}")
        print(f"  ¿Tenés servidor_webhooks.py corriendo en otra terminal?")


asyncio.run(main())
