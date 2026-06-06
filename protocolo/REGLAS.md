# Reglas del protocolo

Vista consolidada de todas las reglas, separadas por capa de enforcement.

## 🔒 Capa MECÁNICA (enforced por hooks/scripts — no se pueden saltear)

| Regla | Cómo se enforza | Archivo |
|-------|-----------------|---------|
| Nunca force-push a la rama protegida (`main`) | Hook bloquea push | `protocolo/hooks/pre-push` |
| Nunca borrar la rama protegida remotamente | Hook bloquea push | `protocolo/hooks/pre-push` |
| Lockear archivos modificados antes de commit (LFS) | Hook bloquea commit | `protocolo/hooks/pre-commit` |
| `feat(vX.X.X/slug)` requiere ítem en HEAD del roadmap | Hook bloquea commit | `protocolo/hooks/commit-msg` |
| Bash bloqueado para comandos destructivos (`git reset --hard origin/main`, `filter-branch`, etc) | Permisos deny | `.claude/settings.json` del proyecto |
| Pre-flight check obligatorio al abrir sesión | SessionStart hook auto-corre | `protocolo/scripts/preflight.sh` |
| Auto-switch a `draft` si arranca en `main` con tree limpio | Preflight | `protocolo/scripts/preflight.sh` |
| Liberar locks LFS fantasma al inicio de sesión | Preflight ejecuta `unlock-stale.sh --apply` | `protocolo/scripts/preflight.sh` |
| Auto-pull main/draft si están behind y tree limpio | Preflight | `protocolo/scripts/preflight.sh` |
| Auto-borrar ramas locales mergeadas a origin | Preflight | `protocolo/scripts/preflight.sh` |

## ⚠️ Capa de TEXTO (requiere juicio del AI — documentadas para minimizar drift)

### Antes de codear cualquier cosa

| Regla | Cuándo | Qué exige |
|-------|--------|-----------|
| **WHY CHECK (sesión)** | Primer mensaje de cualquier sesión que toque código | 4 líneas: tarea, parte del producto, cómo acerca a la métrica única, qué se pierde si no |
| **WHY BRIEF (feature)** | Antes de cualquier feature nueva | 6 líneas: qué, why, métrica, riesgo si no, riesgo si mal, verificable cómo |
| **ROADMAP CHECK** | Antes de proponer o codear comportamiento nuevo | ¿está en el roadmap? Si no → ítem primero (chore), después código (feat) |
| **ROADMAP HEALTH CHECK** | Cada vez que se lee el roadmap | Detectar versiones sin walkthrough y reportar al founder |
| **FEATURE IMPACT CHECK** | Antes de codear feature nueva | Sección 4 del PRODUCT-STATE-BRIEF del proyecto |

### Dónde va cada tipo de cambio

| Tipo de commit | Dónde se registra |
|---------------|-------------------|
| `feat(vX.X.X/slug)` | Roadmap sección Construido + evidence con SHA |
| `fix(vX.X.X/slug)` | REGISTRO-ERRORES con código E## |
| `chore(vX.X.X/slug)` | Solo el commit message |
| `refactor(vX.X.X/slug)` | Sin registro adicional |

### Reglas operativas

| Regla | Qué dice |
|-------|----------|
| **Todo commit toca versión + feature, sin excepción** | Incluso fixes e infra declaran `vX.X.X/slug` |
| **Solo `main` y `draft` viven localmente** | Claude no crea ramas |
| **La rama protegida es sagrada** | Push directo solo para admin. Default es la rama de trabajo |
| **Commits chicos y frecuentes** | El commit es el checkpoint, no el PR |
| **NUNCA `git commit --no-verify`** | Si el hook bloquea, lockear y reintentar — nunca bypassear |
| **NUNCA crear markdowns para info operacional** | Setup, runbooks transitorios, pasos de un solo uso → chat. Markdown solo para arquitectura, decisiones permanentes, protocolos |
| **Excepción: si el founder pide markdown explícitamente, se hace** | La regla anterior es default cuando el AI decide solo |
| **QA-UX Paso F usa Paladin QA exclusivamente** | `mcp__paladin-qa__*` para caminar el producto como usuario real. `mcp__Claude_Preview__*` es verificación técnica (compila/responde) — no es QA de usuario y nunca se usa en el Paso F del skill |

### Reglas de ciclo de sesión

| Momento | Qué hace Claude |
|---------|----------------|
| **Al EMPEZAR** | Leer STATUS.md, REGISTRO-ERRORES.md. Verificar locks. WHY CHECK obligatorio si toca código |
| **Al TERMINAR** | Unlock todos los archivos lockeados. Agregar línea en "Historial de sesiones" de STATUS.md. Actualizar registros tocados |

## 🎯 Frases del founder que disparan comportamiento específico

| Si decís... | Claude hace... |
|-------------|----------------|
| "dame el roadmap" / "cómo vamos" | Lee el roadmap, responde en formato visual sin jerga |
| "cerrá la versión" | Sigue protocolo de cierre, no taggea sin walkthrough visual |
| "qué se ha hecho?" / "ponme al día" | Lee STATUS.md + REGISTRO-ERRORES, resumen ejecutivo |
| "seguí arreglando errores" | Elige el siguiente error no resuelto de mayor severidad |
| "deployá" | Verifica fixes listos, deploya, regenera reporte QA |
| "/why" | Para todo y reporta a qué parte del why sirve lo que está haciendo |
| "stop, falta WHY CHECK" o "stop, falta ROADMAP CHECK" | Hace el check retroactivamente antes de seguir |
| "decidí tú" | Ejecuta sin preguntar opciones. **NO saltea pasos estructurales del protocolo** |
