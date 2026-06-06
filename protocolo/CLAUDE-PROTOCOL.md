# Bloque para CLAUDE.md del proyecto

Este es el bloque que se pega en el `CLAUDE.md` del proyecto que adopte
el protocolo. Documenta las reglas que el AI debe seguir.

---

```markdown
## 🔒 Qué está enforceado por hooks vs qué es texto

Los hooks corren en el harness — el AI no los puede saltear, ni bajo presión,
ni cuando el founder dice "decidí tú". El texto del protocolo depende del
juicio del AI y puede fallar.

Ver `protocolo/REGLAS.md` para la vista consolidada.

**Lo crítico que el AI debe recordar:**

1. **WHY CHECK al inicio de cada sesión que toque código** (texto, 4 líneas).
2. **WHY BRIEF antes de cualquier feature nueva** (texto, 6 líneas).
3. **ROADMAP CHECK antes de codear comportamiento nuevo** (el hook lo enforza al commit).
4. **Dos commits separados:** primero chore con el ítem en roadmap, después feat con el código.
5. **NUNCA crear markdowns para info operacional** — pasos de un solo uso, setup,
   runbooks transitorios van al chat. Markdown solo para arquitectura, decisiones
   permanentes, protocolos.
6. **NUNCA `git commit --no-verify`** — si el hook bloquea, resolver, no bypassear.
7. **Trabajar siempre en `draft`, nunca en `main`** — el preflight auto-corrige
   si arrancás en main por accidente.

**Si el founder dice "decidí tú":** ejecutá sin preguntar opciones, pero
**NO saltees pasos estructurales del protocolo** (WHY CHECK, ROADMAP CHECK,
chore antes de feat). "Decidí tú" significa "no preguntes opciones", no
significa "saltate el protocolo".

## ⚠️ REGLA INVIOLABLE — NUNCA crear markdowns para info operacional

Si tenés que pasarle al founder instrucciones de configuración, pasos manuales,
comandos de un solo uso, o explicación de algo que él va a hacer una vez:
**va al chat, no a un archivo.**

| ✅ SÍ markdown | ❌ NO markdown |
|---------------|---------------|
| Arquitectura del sistema | Setup de una API key nueva |
| Decisiones de producto permanentes | "Los 3 pasos para deployar hoy" |
| Protocolos de colaboración | Runbook transitorio de migración |
| Why del producto | Comandos para probar un cambio puntual |

Si dudás: ¿esto se va a leer más de una vez en los próximos 6 meses?
→ Sí → markdown. → No → chat.

Si el founder pide explícitamente un markdown: lo hacés. Esta regla es
default cuando el AI decide por su cuenta.
```

---

## Cómo usar este bloque

1. Copiá el contenido entre los `---` (sin los backticks que delimitan el código).
2. Pegalo en el `CLAUDE.md` del proyecto, cerca del inicio (después del título y antes de las reglas específicas del producto).
3. Ajustá referencias específicas del proyecto si hace falta (por ejemplo: si la rama default no se llama `draft`).
