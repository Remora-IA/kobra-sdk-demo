# Roadmap — kobra-sdk-demo

## 🟣 v0.3.0 — SDK opinionado: cero fricción para el developer

- [ ] Backend implementa `iniciar_cobranza` idempotente (ver `docs/decisiones/sdk-opinionado.md`)
- [ ] SDK elimina `CobranzaYaActiva` del flujo principal
- [ ] Demo: matriz de pruebas colapsa de 14 filas a 5

## 🔵 v0.2.0 — SDK sync-first con endpoints completos ✓

- [x] Corregir path `/cobranza` → `/cobranzas` (bug vs OpenAPI spec)
- [x] Agregar 4 endpoints faltantes: listar, detalle, cancelar, bulk
- [x] API sync — eliminar `asyncio.run()` de los escenarios
- [x] Respuestas tipadas con dataclasses (`CobranzaResponse`, `WebhookResponse`, `StatusResponse`)

## 🟡 v0.1.0 — Prueba y corrección end-to-end ✓

- [x] Verificar los 4 escenarios contra el backend real (kobra.remora-ia.com)
- [x] Corregir lo que falle (scripts, README, kobra.py)
- [x] Confirmar que el README coincide exactamente con lo que pasa al correrlo
