# Roadmap — kobra-sdk-demo

## 🔵 v0.2.0 — SDK sync-first con endpoints completos

- [ ] Corregir path `/cobranza` → `/cobranzas` (bug vs OpenAPI spec)
- [ ] Agregar 4 endpoints faltantes: listar, detalle, cancelar, bulk
- [ ] API sync — eliminar `asyncio.run()` de los escenarios
- [ ] Respuestas tipadas con dataclasses (`CobranzaResponse`, `WebhookResponse`, `StatusResponse`)

## 🟡 v0.1.0 — Prueba y corrección end-to-end

- [ ] Verificar los 4 escenarios contra el backend real (kobra.remora-ia.com)
- [ ] Corregir lo que falle (scripts, README, kobra.py)
- [ ] Confirmar que el README coincide exactamente con lo que pasa al correrlo
