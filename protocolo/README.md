# Protocolo de colaboración AI + founder

Protocolo portable para que un founder no técnico y sesiones de Claude Code
trabajen sobre el mismo repositorio sin pisarse, sin drift, y sin que el
founder tenga que recordar comandos antes de cada sesión.

## Qué resuelve

Sesiones de Claude Code no tienen memoria entre turnos. El protocolo
convierte rituales que dependerían de "recordar" en **enforcement
mecánico** (hooks de git) o **rituales documentados** (texto en CLAUDE.md
que el AI lee cada vez). El resultado: cualquier sesión nueva arranca
con el mismo contexto y las mismas restricciones, sin que el founder
tenga que repetir nada.

## Qué hay adentro

```
protocolo/
├── README.md            # este archivo
├── REGLAS.md            # las reglas del protocolo, vista consolidada
├── CLAUDE-PROTOCOL.md   # bloque para pegar en el CLAUDE.md del proyecto
├── config.sh            # variables que cada proyecto setea
├── install.sh           # instala el protocolo en el repo actual
├── hooks/
│   ├── pre-commit       # exige LFS lock antes de modificar archivos
│   ├── pre-push         # bloquea force-push y delete de la rama protegida
│   └── commit-msg       # exige ítem en roadmap para feat commits
└── scripts/
    ├── preflight.sh     # ritual obligatorio al abrir sesión (auto-fix + alertas)
    └── unlock-stale.sh  # libera locks LFS fantasma de sesiones que murieron sin cerrar
```

## Instalación en un proyecto nuevo

```bash
# Desde el repo donde querés activar el protocolo
cd mi-proyecto/

# 1. Clonar/copiar la carpeta protocolo/
# (Cuando el protocolo viva en su propio repo, será: git clone <url> protocolo)

# 2. Editar protocolo/config.sh con las rutas de tu proyecto
$EDITOR protocolo/config.sh

# 3. Correr el instalador
bash protocolo/install.sh

# 4. Agregar el bloque de CLAUDE-PROTOCOL.md al CLAUDE.md de tu proyecto

# 5. Verificar que el SessionStart hook está configurado en .claude/settings.json
# (apunta a scripts/preflight.sh)
```

## Configuración (`config.sh`)

| Variable | Default | Qué controla |
|----------|---------|--------------|
| `PROTECTED_BRANCH` | `main` | Rama que nunca se commitea directo (la que se deploya) |
| `DEFAULT_BRANCH` | `draft` | Rama donde trabajan las sesiones de Claude |
| `ROADMAP_PATH` | `docs/roadmap.md` | Donde vive el roadmap del producto |
| `ERRORES_PATH` | `docs/REGISTRO-ERRORES.md` | Journal de bugs con código E## |
| `STATUS_PATH` | `docs/STATUS.md` | Estado entre sesiones |
| `WHY_PATH` | `docs/WHY.md` | El "why" del producto |
| `DOMAIN_STOP_WORDS` | (palabras de Kobra) | Palabras comunes del dominio a excluir del matching del hook commit-msg |

## Por qué dos capas

**Hooks (mecánico):** el AI no los puede saltear ni bajo presión.
- `pre-push`: no force-push a main
- `pre-commit`: lockear antes de editar (LFS coordination)
- `commit-msg`: feat requiere ítem en roadmap

**Texto (juicio del AI):** documentado para que el AI lo aplique consistentemente.
- WHY CHECK: ¿esto sirve al why del producto?
- WHY BRIEF: ¿esta feature está justificada?
- ROADMAP CHECK: ¿está autorizada esta feature?
- "Info operacional al chat, no a markdown"

La regla de oro del meta-protocolo: **lo que puede ser hook, debe ser
hook.** Texto solo para lo que genuinamente requiere razonamiento sobre
el negocio.

## Cómo evoluciona el protocolo

Cada cambio al protocolo es un commit dentro de `protocolo/`. Cuando esta
carpeta se promueva a su propio repo (`Remora-IA/claude-protocol` o
similar), los cambios viven ahí y se propagan a cada proyecto que use el
protocolo con un `git pull` en `protocolo/`.

Mientras tanto, viviendo dentro de Kobra, los cambios al protocolo van
junto con los commits normales del proyecto, pero todos bajo el slug
`protocolo-portable` o slugs específicos (`commit-msg-hook`,
`unlock-stale`, etc) para mantener la trazabilidad.

## Origen

Este protocolo nació en el proyecto Kobra (Remora-IA) durante junio 2026,
después de observar repetidamente cómo sesiones de Claude perdían el why,
mezclaban scope, saltaban pasos críticos bajo presión ("decidí tú"), y
dejaban trabajo a medias (locks sin liberar, archivos sin commitear).

Cada hook y cada regla acá responde a un incidente concreto observado.
No es teórico — es lo que funcionó.
