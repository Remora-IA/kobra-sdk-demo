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

import hashlib
import hmac
import os
from datetime import datetime

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Header, HTTPException

load_dotenv()

app = FastAPI(title="Sistema Somos Rentable — receptor de webhooks Kobra")

# Secreto para verificar la firma de Kobra.
# Lo recibís UNA SOLA VEZ al registrar el webhook con kobra.registrar_webhook().
# Guardalo en tu .env como KOBRA_SIGNING_SECRET.
KOBRA_SIGNING_SECRET = os.environ.get("KOBRA_SIGNING_SECRET", "")

# Simulación de la base de datos de Somos Rentable
# En producción: esto sería una query a su base de datos real
_mi_base_de_datos: dict[str, dict] = {
    "SR-12345": {"nombre": "Juan Pérez",      "deuda": 150000, "estado": "PENDIENTE"},
    "SR-99999": {"nombre": "María González",  "deuda":  85000, "estado": "PENDIENTE"},
}


def _verificar_firma(body_bytes: bytes, signature_header: str | None) -> bool:
    """
    Verifica que el webhook viene realmente de Kobra.

    Kobra firma cada request con HMAC-SHA256 usando tu signing_secret.
    El header X-Kobra-Signature tiene el formato: "sha256=<hex>"

    Si no tenés KOBRA_SIGNING_SECRET configurado, se omite la verificación
    (útil en desarrollo local con el simulador).
    """
    if not KOBRA_SIGNING_SECRET:
        return True  # sin secreto configurado, aceptar todo (modo dev)
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        KOBRA_SIGNING_SECRET.encode(),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


@app.post("/webhooks/kobra")
async def recibir_evento_kobra(
    request: Request,
    x_kobra_signature: str | None = Header(default=None),
    x_kobra_event: str | None = Header(default=None),
) -> dict:
    """
    Kobra llama a este endpoint cuando ocurre un evento.

    Eventos posibles:
      - cobrado      — el pago fue verificado contra el banco
      - acuerdo      — el deudor prometió pagar (el dinero todavía no llegó)
      - no_responde  — Carolina agotó los intentos sin respuesta
      - cancelado    — la cobranza fue cancelada (por vos o por Kobra)
    """
    body_bytes = await request.body()

    if not _verificar_firma(body_bytes, x_kobra_signature):
        raise HTTPException(status_code=401, detail="Firma inválida")

    evento = await request.json()
    ahora = datetime.now().strftime("%H:%M:%S")

    print(f"\n{'='*50}")
    print(f"[{ahora}] EVENTO RECIBIDO DE KOBRA")
    print(f"{'='*50}")
    print(f"  evento:          {evento.get('evento')}")
    print(f"  deudor_id:       {evento.get('deudor_id')}")
    print(f"  conversation_id: {evento.get('conversation_id')}")
    print(f"  timestamp:       {evento.get('timestamp')}")

    tipo = evento.get("evento")

    if tipo == "cobrado":
        monto = evento.get("monto", 0)
        print(f"  monto:           ${monto:,.0f}".replace(",", "."))
        _procesar_pago_confirmado(evento)

    elif tipo == "acuerdo":
        monto = evento.get("monto_acordado", 0)
        fecha = evento.get("fecha_pago_acordada", "sin fecha")
        link = evento.get("link_pago")
        print(f"  monto_acordado:  ${monto:,.0f}".replace(",", "."))
        print(f"  fecha acordada:  {fecha}")
        if link:
            print(f"  link_pago:       {link}")
        _procesar_acuerdo(evento)

    elif tipo == "no_responde":
        intentos = evento.get("intentos", "?")
        print(f"  intentos:        {intentos}")
        _procesar_sin_respuesta(evento)

    elif tipo == "cancelado":
        motivo = evento.get("motivo", "sin motivo")
        print(f"  motivo:          {motivo}")
        _procesar_cancelado(evento)

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
        print(f"  [!] deudor_id {deudor_id!r} no encontrado — guardando para auditoría")


def _procesar_acuerdo(evento: dict) -> None:
    """Registra un compromiso de pago cuando el deudor promete pagar."""
    deudor_id = evento.get("deudor_id")
    fecha = evento.get("fecha_pago_acordada", "sin fecha")

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


def _procesar_sin_respuesta(evento: dict) -> None:
    """Registra que Carolina agotó intentos sin respuesta del deudor."""
    deudor_id = evento.get("deudor_id")

    if deudor_id in _mi_base_de_datos:
        registro = _mi_base_de_datos[deudor_id]
        registro["estado"] = "SIN_RESPUESTA"
        print(f"\n  → Registrando sin respuesta...")
        print(f"    {deudor_id} ({registro['nombre']}): → SIN_RESPUESTA")
        print(f"  ✓ Caso marcado para seguimiento manual")
    else:
        print(f"  [!] deudor_id {deudor_id!r} no encontrado")


def _procesar_cancelado(evento: dict) -> None:
    """Registra la cancelación de una cobranza."""
    deudor_id = evento.get("deudor_id")
    motivo = evento.get("motivo", "sin motivo")

    if deudor_id in _mi_base_de_datos:
        registro = _mi_base_de_datos[deudor_id]
        registro["estado"] = "CANCELADO"
        registro["motivo_cancelacion"] = motivo
        print(f"\n  → Registrando cancelación...")
        print(f"    {deudor_id} ({registro['nombre']}): → CANCELADO ({motivo})")
        print(f"  ✓ Cobranza cancelada")
    else:
        print(f"  [!] deudor_id {deudor_id!r} no encontrado")


@app.get("/")
async def home() -> dict:
    """Estado actual de nuestra base de datos (para monitoreo durante la demo)."""
    return {
        "sistema": "Somos Rentable — receptor de webhooks Kobra",
        "firma_configurada": bool(KOBRA_SIGNING_SECRET),
        "deudores": _mi_base_de_datos,
    }


if __name__ == "__main__":
    puerto = int(os.environ.get("WEBHOOK_LOCAL_PORT", 8000))
    print(f"\n{'='*50}")
    print(f"Sistema Somos Rentable levantado")
    print(f"Escuchando webhooks de Kobra en: http://localhost:{puerto}/webhooks/kobra")
    print(f"Ver estado de la base de datos:  http://localhost:{puerto}/")
    if not KOBRA_SIGNING_SECRET:
        print(f"\n  ⚠  KOBRA_SIGNING_SECRET no configurado.")
        print(f"     Verificación de firma desactivada (modo dev).")
        print(f"     En producción: agregá KOBRA_SIGNING_SECRET a tu .env")
    print(f"{'='*50}\n")
    uvicorn.run(app, host="0.0.0.0", port=puerto, log_level="warning")
