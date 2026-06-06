# Kobra SDK — Guía para el desarrollador de Somos Rentable

## La situación

Sos el dev de Somos Rentable. Tu PM te pasó este ticket:

> "Cuando un cliente no paga en 30 días, Kobra tiene que contactarlo por WhatsApp
> automáticamente. Y cuando el cliente paga, nuestro sistema tiene que saberlo
> para actualizar su estado."

Esta guía te lleva de cero a integración funcionando. No necesitás instalar
nada especial — Kobra es una API REST. Si sabés hacer un `POST`, podés usar Kobra.

---

## Lo que Kobra hace por vos

```
Tu sistema                          Kobra                        Tu cliente (deudor)
---------                           -----                        ------------------
Vence una cuota
    │
    ├──► POST /api/sdk/cobranza ──► Carolina arranca ──────────► WhatsApp: "Hola Juan,
    │                                                              te escribimos sobre..."
    │
    │    (días después, el cliente paga)
    │
    ◄──── POST a tu webhook ◄────── Kobra detecta el pago
         {"evento": "cobrado",
          "deudor_id": "SR-12345",
          "monto": 150000}
    │
    ▼
Tu sistema marca la deuda como pagada
```

Eso es todo. Dos llamadas. El resto lo hace Kobra.

---

## Antes de empezar

Necesitás dos cosas que te da el equipo de Kobra:

```
KOBRA_API_KEY=...         ← tu clave de acceso
KOBRA_BASE_URL=https://kobra-backend-760602975866.us-central1.run.app
```

Copialas en un archivo `.env` en este directorio:

```bash
cp .env.example .env
# Editá .env y pegá los valores que te dieron
```

---

## Instalación (2 minutos)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Paso 1 — Registrar tu webhook

Lo primero: decirle a Kobra a dónde avisarte cuando pase algo.

```bash
python3 escenarios/01_registrar_webhook.py
```

Qué hace: le dice a Kobra "cuando un cliente pague o haga un acuerdo, mandá un
POST a esta URL". Solo necesitás hacerlo una vez.

Para desarrollo local, el script usa `ngrok` o `localtunnel` para exponer tu
puerto 8000 a internet. En producción, ponés la URL de tu sistema directamente.

---

## Paso 2 — Disparar una cobranza

Cuando vence una cuota en tu sistema, llamás a Kobra:

```bash
python3 escenarios/02_iniciar_cobranza.py
```

Qué pasa después de correrlo:
- Kobra crea la conversación internamente
- Carolina le manda un WhatsApp al deudor en segundos
- Tu sistema recibe un `conversation_id` para rastrear el caso
- No tenés que hacer nada más — Carolina negocia sola

---

## Paso 3 — Recibir eventos de vuelta

Cuando el cliente paga (o promete pagar), Kobra llama a tu webhook.

```bash
# Terminal 1: levantá el receptor de webhooks
python3 servidor_webhooks.py

# Terminal 2: simulá que Kobra manda un evento
python3 escenarios/03_simular_evento.py
```

Qué ves en la terminal del servidor:
```
[EVENTO] cobrado
  deudor_id:  SR-12345
  monto:      $150.000
  timestamp:  2026-06-09T15:30:00Z
→ Marcando deuda SR-12345 como pagada en nuestra base de datos...
✓ Listo
```

---

## Paso 4 — Flujo completo end-to-end

Este escenario corre todo junto: dispara la cobranza, levanta el servidor de
webhooks, y simula el pago para que veas el ciclo completo en una sola terminal.

```bash
python3 escenarios/04_flujo_completo.py
```

---

## Referencia rápida de la API

### Iniciar cobranza

```
POST /api/sdk/cobranza
Header: X-Kobra-Api-Key: <tu-key>

Body:
{
  "deudor_id": "SR-12345",        ← tu ID interno (lo recibís de vuelta en los webhooks)
  "nombre":    "Juan Pérez",
  "telefono":  "+56912345678",    ← formato E.164, con código de país
  "monto":     150000,            ← pesos chilenos, sin decimales
  "concepto":  "Cuota octubre"    ← opcional, aparece en el comprobante
}

Respuesta exitosa (201):
{
  "ok":              true,
  "conversation_id": "a1b2c3d4",   ← guardalo si querés rastrear el caso
  "deudor_id":       "SR-12345",
  "estado":          "iniciada",
  "primer_mensaje":  "Hola Juan, te contactamos de parte de..."
}

Error si ya hay una cobranza activa para ese teléfono (409):
{
  "detail": "Ya existe una cobranza activa para este teléfono (conversation_id: ...)"
}
```

### Registrar webhook

```
PUT /api/sdk/webhook
Header: X-Kobra-Api-Key: <tu-key>

Body:
{
  "url":     "https://tusistema.cl/webhooks/kobra",
  "eventos": ["cobrado", "acuerdo"]   ← opcional, default: todos
}

Respuesta (200):
{
  "ok":     true,
  "url":    "https://tusistema.cl/webhooks/kobra",
  "eventos": ["acuerdo", "cobrado"]
}
```

### Webhooks que recibís

**on_cobrado** — el pago fue confirmado:
```json
{
  "evento":          "cobrado",
  "conversation_id": "a1b2c3d4",
  "deudor_id":       "SR-12345",
  "monto":           150000,
  "timestamp":       "2026-06-09T15:30:00Z"
}
```

**on_acuerdo** — el deudor prometió pagar (el pago todavía no llegó):
```json
{
  "evento":          "acuerdo",
  "conversation_id": "a1b2c3d4",
  "deudor_id":       "SR-12345",
  "monto_acordado":  150000,
  "fecha_pago":      "2026-06-15",
  "link_pago":       "https://khipu.com/payment/...",
  "timestamp":       "2026-06-09T14:00:00Z"
}
```

### Health check (sin auth)

```
GET /api/sdk/status

Respuesta:
{
  "sdk_version":       "0.5.0",
  "configurado":       true,
  "webhooks_activos":  1
}
```

---

## Errores comunes

| Error | Causa | Solución |
|-------|-------|----------|
| `401 API key inválida` | Key incorrecta o falta el header | Verificar que `X-Kobra-Api-Key` lleva el valor correcto |
| `503 SDK no configurado` | El servidor de Kobra no tiene la key configurada | Avisar al equipo de Kobra |
| `409 cobranza activa` | Ya hay una conversación en curso para ese teléfono | Esperar a que termine, o usar `conversation_id` para rastrearla |
| Webhook no llega | Tu URL no es pública | Usar ngrok en desarrollo; URL real en producción |

---

## Preguntas frecuentes

**¿Kobra ve nuestra base de datos?**
No. Kobra solo recibe lo que vos le mandás: nombre, teléfono, monto, y un ID tuyo.
Tu base de datos sigue siendo tuya.

**¿Qué pasa si el deudor no responde?**
Carolina tiene un protocolo para eso. No necesitás hacer nada — Kobra lo maneja.

**¿Podemos tener múltiples cobranzas activas al mismo tiempo?**
Sí. Cada llamada a `/cobranza` crea una conversación independiente.
El límite es: un deudor activo por número de teléfono.

**¿Cómo sé si una cobranza está en progreso?**
Guardás el `conversation_id` que te devuelve `/cobranza`. Podés consultarlo
(próxima versión del SDK incluirá `GET /api/sdk/cobranza/{id}/estado`).

**¿Qué pasa si nuestro webhook falla?**
Kobra hace el intento y loguea el error. Hoy no hay reintentos automáticos —
si necesitás garantía de entrega, implementá idempotencia en tu receptor.
