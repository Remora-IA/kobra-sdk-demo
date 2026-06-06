# STATUS — kobra-sdk-demo

## Estado actual

v0.2.0 completo. Prueba end-to-end de los 4 escenarios: OK. SDK validado contra el backend real.

## Historial de sesiones

| Fecha | Qué se hizo |
|-------|-------------|
| 2026-06-06 | Instalación del protocolo de colaboración AI+founder |
| 2026-06-06 | SDK reescrito: sync-first, paths corregidos (/cobranzas), 4 endpoints nuevos, respuestas tipadas |
| 2026-06-06 | Docs Fern publicadas — actualizados: signing_secret, X-Kobra-Signature, eventos no_responde/cancelado, params listar |
| 2026-06-06 | Decisión de diseño: SDK opinionado — iniciar_cobranza idempotente (docs/decisiones/sdk-opinionado.md) |
| 2026-06-06 | Prueba end-to-end contra backend real: 4 escenarios OK. iniciar_cobranza (201), CobranzaYaActiva (409+existing_id), flujo completo. venv creado. |
