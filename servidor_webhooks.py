"""
servidor_webhooks.py — el sistema de Somos Rentable que recibe eventos de Kobra.

Levantarlo en una terminal:
    python3 servidor_webhooks.py

Esto simula lo que Somos Rentable implementaría en su propio backend.
Cuando Kobra detecta un pago o un acuerdo, llama a este servidor.

En producción, este código viviría dentro del sistema de Somos Rentable
(Django, Rails, Express, lo que sea) como un endpoint más.
"""

from __future__ import annotations

import os
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request

load_dotenv()

app = FastAPI(title="Sistema Somos Rentable — receptor de webhooks Kobra")

# Simulación de la base de datos de Somos Rentable
# En producción: esto sería una query a su base de datos real
_mi_base_de_datos: dict[str, dict] = {
    "SR-12345": {"nombre": "Juan Pérez",      "deuda": 150000, "estado": "PENDIENTE"},
    "SR-99999": {"nombre": "María González",  "deuda":  85000, "estado": "PENDIENTE"},
}


@app.post("/webhooks/kobra")
async def recibir_evento_kobra(request: Request) -> dict:
    """
    Kobra llama a este endpoint cuando ocurre un evento.

    Eventos posibles:
      - cobrado: el pago fue verificado
      - acuerdo: el deudor prometió pagar (el pago todavía no llegó)
    """
    evento = await request.json()
    ahora = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'='*50}")
    print(f"[{ahora}] EVENTO RECIBIDO DE KOBRA")
    print(f"{'='*50}")
    print(f"  evento:          {evento.get('evento')}")
    print(f"  deudor_id:       {evento.get('deudor_id')}")
    print(f"  conversation_id: {evento.get('conversation_id')}")
    print(f"  timestamp:       {evento.get('timestamp')}")

    if evento.get("evento") == "cobrado":
        monto = evento.get("monto", 0)
        print(f"  monto:           ${monto:,.0f}".replace(",", "."))
        _procesar_pago_confirmado(evento)

    elif evento.get("evento") == "acuerdo":
        monto = evento.get("monto_acordado", 0)
        fecha = evento.get("fecha_pago", "sin fecha")
        link = evento.get("link_pago")
        print(f"  monto_acordado:  ${monto:,.0f}".replace(",", "."))
        print(f"  fecha_pago:      {fecha}")
        if link:
            print(f"  link_pago:       {link}")
        _procesar_acuerdo(evento)

    else:
        print(f"  [!] Evento desconocido — ignorado")

    print(f"{'='*50}\n")
    return {"ok": True}


def _procesar_pago_confirmado(evento: dict) -> None:
    """Actualiza nuestra base de datos cuando Kobra confirma un pago."""
    deudor_id = evento.get("deudor_id")
    monto = evento.get("monto", 0)

    if deudor_id in _mi_base_de_datos:
        registro = _mi_base_de_datos[deudor_id]
        registro["estado"] = "PAGADO"
        registro["monto_cobrado"] = monto
        registro["fecha_pago"] = evento.get("timestamp")
        print(f"\n  → Actualizando base de datos...")
        print(f"    {deudor_id} ({registro['nombre']}): PENDIENTE → PAGADO")
        print(f"    Monto: ${monto:,.0f}".replace(",", "."))
        print(f"  ✓ Base de datos actualizada")
    else:
        print(f"  [!] deudor_id {deudor_id!r} no encontrado en nuestra base de datos")
        print(f"      Guardando igualmente para auditoría...")


def _procesar_acuerdo(evento: dict) -> None:
    """Registra un compromiso de pago cuando el deudor promete pagar."""
    deudor_id = evento.get("deudor_id")
    fecha = evento.get("fecha_pago", "sin fecha")

    if deudor_id in _mi_base_de_datos:
        registro = _mi_base_de_datos[deudor_id]
        registro["estado"] = "COMPROMETIDO"
        registro["fecha_compromiso"] = fecha
        print(f"\n  → Registrando compromiso...")
        print(f"    {deudor_id} ({registro['nombre']}): PENDIENTE → COMPROMETIDO")
        print(f"    Fecha de pago prometida: {fecha}")
        print(f"  ✓ Compromiso registrado — esperando confirmación bancaria")
    else:
        print(f"  [!] deudor_id {deudor_id!r} no encontrado")


@app.get("/")
async def home() -> dict:
    """Estado actual de nuestra base de datos (para monitoreo durante la demo)."""
    return {
        "sistema": "Somos Rentable — receptor de webhooks Kobra",
        "deudores": _mi_base_de_datos,
    }


if __name__ == "__main__":
    puerto = int(os.environ.get("WEBHOOK_LOCAL_PORT", 8000))
    print(f"\n{'='*50}")
    print(f"Sistema Somos Rentable levantado")
    print(f"Escuchando webhooks de Kobra en: http://localhost:{puerto}/webhooks/kobra")
    print(f"Ver estado de la base de datos:  http://localhost:{puerto}/")
    print(f"{'='*50}\n")
    uvicorn.run(app, host="0.0.0.0", port=puerto, log_level="warning")
