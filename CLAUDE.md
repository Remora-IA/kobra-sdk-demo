# CLAUDE.md — kobra-sdk-demo

Este repo es el kit de integración que recibe el primer desarrollador que conecta Kobra.
La métrica única: **tiempo hasta primer webhook recibido**.

---

## Por qué existe

Ver `docs/WHY.md`.

---

## Protocolo de colaboración AI+founder

### Lo que enforzan los hooks (mecánico — no se puede saltear)

| Regla | Hook |
|-------|------|
| Nunca force-push a `main` | `protocolo/hooks/pre-push` |
| Nunca borrar `main` desde remote | `protocolo/hooks/pre-push` |
| `feat(v0.X.X/slug)` requiere ítem en `docs/roadmap.md` | `protocolo/hooks/commit-msg` |

### Lo que depende del juicio del AI (texto)

1. **WHY CHECK al inicio de cada sesión que toque código** — ¿qué tarea?, ¿acerca a la métrica única?, ¿qué se pierde si no?
2. **ROADMAP CHECK antes de cualquier cambio** — ¿está en `docs/roadmap.md`? Si no, primer commit solo agrega el ítem (`chore`), después viene el código (`feat`).
3. **NUNCA `git commit --no-verify`** — si el hook bloquea, resolver, no bypassear.
4. **NUNCA crear markdowns para info operacional** — pasos de un solo uso, setup, runbooks transitorios van al chat. Markdown solo para arquitectura, decisiones permanentes, protocolos.

### Reglas de sesión

| Momento | Qué hace Claude |
|---------|----------------|
| Al EMPEZAR | Leer `docs/STATUS.md`. WHY CHECK si toca código. |
| Al TERMINAR | Agregar línea en "Historial de sesiones" de `docs/STATUS.md`. |

### Si el founder dice "decidí tú"

Ejecutar sin preguntar opciones. **NO saltear WHY CHECK ni ROADMAP CHECK** — "decidí tú" significa "no preguntes opciones", no "saltate el protocolo".
