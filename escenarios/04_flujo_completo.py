"""
Escenario 4 — Flujo completo end-to-end.

Este script simula el ciclo entero:

  1. Sistema de Somos Rentable detecta que una cuota venció
  2. Llama a Kobra para iniciar la cobranza
  3. Carolina contacta al deudor por WhatsApp (en el backend real)
  4. (simulado) El deudor paga
  5. Kobra dispara el webhook on_cobrado al sistema de Somos Rentable
  6. El sistema de Somos Rentable actualiza su base de datos

Lo que NO simula (porque requieren el backend real corriendo):
  - El mensaje real de WhatsApp al deudor
  - La conversación de Carolina con el deudor
  - La verificación bancaria del pago

Para el paso 5, levanta un servidor de webhooks local temporalmente.

Correr:
    python3 escenarios/04_flujo_completo.py
"""

import asyncio
import os
import sys
import threading
from datetime import datetime, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

from kobra import KobraClient, CobranzaYaActiva, KobraError

load_dotenv()

# -----------------------------------------------------------------------
# Simulación de la base de datos de Somos Rentable
# -----------------------------------------------------------------------
mi_base_de_datos = {
    "SR-12345": {"nombre": "Juan Pérez", "deuda": 150000, "estado": "PENDIENTE"},
}

eventos_recibidos: list[dict] = []

# Servidor de webhooks temporal (corre en background)
webhook_app = FastAPI()


@webhook_app.post("/webhooks/kobra")
async def recibir_webhook(request: Request) -> dict:
    evento = await request.json()
    eventos_recibidos.append(evento)
    return {"ok": True}


def _levantar_servidor(puerto: int) -> None:
    uvicorn.run(webhook_app, host="0.0.0.0", port=puerto, log_level="error")


# -----------------------------------------------------------------------
# Flujo principal
# -----------------------------------------------------------------------

async def main():
    api_key = os.environ.get("KOBRA_API_KEY", "")
    base_url = os.environ.get("KOBRA_BASE_URL", "")
    puerto = int(os.environ.get("WEBHOOK_LOCAL_PORT", 8000))

    if not api_key:
        print("✗ Falta KOBRA_API_KEY en el archivo .env")
        return

    kobra = KobraClient(api_key=api_key, base_url=base_url or None)

    print(f"\n{'='*60}")
    print(f"FLUJO COMPLETO — Kobra SDK Demo")
    print(f"{'='*60}\n")

    # ----------------------------------------------------------------
    # Paso 0: verificar que el SDK está configurado
    # ----------------------------------------------------------------
    print(f"[0/5] Verificando conexión con Kobra...")
    try:
        estado = await kobra.status()
        if not estado.get("configurado"):
            print(f"  ✗ El servidor de Kobra no tiene SDK configurado.")
            print(f"    Pedile al equipo de Kobra que agregue KOBRA_SDK_API_KEY al deploy.")
            return
        print(f"  ✓ Kobra SDK v{estado.get('sdk_version', '?')} — OK\n")
    except Exception as e:
        print(f"  ✗ No se pudo conectar a Kobra: {e}\n")
        return

    # ----------------------------------------------------------------
    # Paso 1: levantar servidor de webhooks local (background)
    # ----------------------------------------------------------------
    print(f"[1/5] Levantando servidor de webhooks local (puerto {puerto})...")
    t = threading.Thread(target=_levantar_servidor, args=(puerto,), daemon=True)
    t.start()
    await asyncio.sleep(1.5)  # esperar que levante
    print(f"  ✓ Servidor listo en http://localhost:{puerto}/webhooks/kobra\n")

    # ----------------------------------------------------------------
    # Paso 2: registrar webhook en Kobra
    # NOTA: en producción, esto sería tu URL pública real, no localhost.
    # Kobra no puede llamar a localhost desde sus servidores.
    # Para demostración local, el paso de webhook es simulado en el paso 5.
    # ----------------------------------------------------------------
    print(f"[2/5] Registrando webhook en Kobra...")
    print(f"  ⚠  En esta demo local, el webhook se simula en el paso 5.")
    print(f"     En producción, registrarías tu URL pública y Kobra la llamaría solo.\n")

    # ----------------------------------------------------------------
    # Paso 3: detectar deuda vencida y disparar cobranza
    # ----------------------------------------------------------------
    print(f"[3/5] Sistema de Somos Rentable detecta cuota vencida...")
    deudor = mi_base_de_datos["SR-12345"]
    print(f"  Deudor:  {deudor['nombre']}")
    print(f"  Deuda:   ${deudor['deuda']:,.0f}".replace(",", "."))
    print(f"  Estado:  {deudor['estado']}")
    print(f"\n  → Llamando a Kobra para iniciar cobranza...\n")

    try:
        resultado = await kobra.iniciar_cobranza(
            deudor_id="SR-12345",
            nombre=deudor["nombre"],
            telefono="+56912345678",
            monto=deudor["deuda"],
            concepto="Cuota octubre 2026 — Proyecto Bello Horizonte",
        )
        conv_id = resultado["conversation_id"]
        print(f"  ✓ Cobranza iniciada — conversation_id: {conv_id}")
        print(f"  Carolina está contactando al deudor por WhatsApp...\n")

    except CobranzaYaActiva:
        conv_id = "EXISTENTE"
        print(f"  ⚠  Ya había una cobranza activa para este número.")
        print(f"     Continuando con la simulación...\n")

    except KobraError as e:
        print(f"  ✗ Error al iniciar cobranza: {e.detail}")
        print(f"\n  ¿El servidor de Kobra está corriendo y tiene KOBRA_SDK_API_KEY configurado?")
        return

    # ----------------------------------------------------------------
    # Paso 4: simular que pasaron días y el deudor pagó
    # ----------------------------------------------------------------
    print(f"[4/5] (Simulando) Han pasado 2 días. El deudor pagó.")
    print(f"  En la realidad: Kobra detecta el pago bancario y dispara el webhook.")
    print(f"  En esta demo:   simulamos el POST que Kobra haría a tu sistema.\n")
    await asyncio.sleep(1)

    # ----------------------------------------------------------------
    # Paso 5: simular webhook on_cobrado
    # ----------------------------------------------------------------
    print(f"[5/5] Simulando webhook on_cobrado de Kobra → tu sistema...")

    payload_cobrado = {
        "evento": "cobrado",
        "conversation_id": conv_id,
        "deudor_id": "SR-12345",
        "monto": 150000,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                f"http://localhost:{puerto}/webhooks/kobra",
                json=payload_cobrado,
            )
            if resp.status_code == 200:
                print(f"  ✓ Webhook recibido por tu sistema")
            else:
                print(f"  ✗ Tu sistema respondió {resp.status_code}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

    # Actualizar base de datos (lo que haría servidor_webhooks.py)
    mi_base_de_datos["SR-12345"]["estado"] = "PAGADO"
    mi_base_de_datos["SR-12345"]["monto_cobrado"] = 150000

    # ----------------------------------------------------------------
    # Resumen
    # ----------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"RESUMEN FINAL")
    print(f"{'='*60}")
    deudor_final = mi_base_de_datos["SR-12345"]
    print(f"  Deudor:         {deudor_final['nombre']}")
    print(f"  Estado final:   {deudor_final['estado']}")
    print(f"  Monto cobrado:  ${deudor_final.get('monto_cobrado', 0):,.0f}".replace(",", "."))
    print(f"\n  Lo que hizo tu sistema: 2 llamadas a Kobra.")
    print(f"  Lo que hizo Kobra: contactar, negociar, confirmar el pago.")
    print(f"  Lo que hizo tu equipo: nada.")
    print(f"{'='*60}\n")


asyncio.run(main())
