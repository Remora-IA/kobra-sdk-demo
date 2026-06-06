#!/usr/bin/env bash
# protocolo/install.sh — instala el protocolo de colaboración AI+founder
# en el repositorio actual.
#
# Qué hace:
#   1. Verifica que estás en la raíz de un repo git.
#   2. Configura core.hooksPath para usar protocolo/hooks/.
#   3. Verifica que config.sh tiene los valores correctos para este proyecto.
#   4. Reporta el estado final.
#
# Idempotente: correrlo varias veces no rompe nada.
#
# Uso:
#   bash protocolo/install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"

if [[ -z "$REPO_ROOT" ]]; then
    echo "✗ ERROR: no estás dentro de un repo git."
    exit 1
fi

cd "$REPO_ROOT"

if [[ ! -d "protocolo" ]]; then
    echo "✗ ERROR: la carpeta protocolo/ no existe en $REPO_ROOT"
    echo "  ¿Estás corriendo desde el repo correcto?"
    exit 1
fi

echo "=== Instalando protocolo en $REPO_ROOT ==="
echo

# 1. core.hooksPath → protocolo/hooks
CURRENT_HOOKS=$(git config --get core.hooksPath 2>/dev/null || echo "")
if [[ "$CURRENT_HOOKS" == "protocolo/hooks" ]]; then
    echo "✓ core.hooksPath ya apunta a protocolo/hooks"
else
    git config core.hooksPath protocolo/hooks
    echo "→ core.hooksPath configurado: protocolo/hooks"
    if [[ -n "$CURRENT_HOOKS" ]]; then
        echo "  (antes era: $CURRENT_HOOKS)"
    fi
fi

# 2. Verificar permisos de ejecución
chmod +x protocolo/hooks/* protocolo/scripts/*
echo "✓ Permisos de ejecución verificados"

# 3. Cargar y mostrar config
if [[ -f protocolo/config.sh ]]; then
    source protocolo/config.sh
    echo
    echo "=== Configuración activa ==="
    echo "  PROTECTED_BRANCH:    $PROTECTED_BRANCH"
    echo "  DEFAULT_BRANCH:      $DEFAULT_BRANCH"
    echo "  ROADMAP_PATH:        $ROADMAP_PATH"
    echo "  ERRORES_PATH:        $ERRORES_PATH"
    echo "  STATUS_PATH:         $STATUS_PATH"
    echo "  WHY_PATH:            $WHY_PATH"

    # Verificar archivos referenciados
    echo
    echo "=== Archivos del proyecto ==="
    for var in ROADMAP_PATH ERRORES_PATH STATUS_PATH WHY_PATH; do
        path="${!var}"
        if [[ -f "$path" ]]; then
            echo "  ✓ $path"
        else
            echo "  ⚠ $path NO existe — crear antes de usar el protocolo"
        fi
    done
else
    echo "⚠ protocolo/config.sh no encontrado — usando defaults"
fi

# 4. Verificar wrapper de preflight
if [[ -f scripts/preflight.sh ]]; then
    if grep -q "protocolo/scripts/preflight.sh" scripts/preflight.sh 2>/dev/null; then
        echo
        echo "✓ scripts/preflight.sh es wrapper del protocolo"
    fi
else
    mkdir -p scripts
    cat > scripts/preflight.sh <<'WRAPPER'
#!/usr/bin/env bash
# Wrapper para compatibilidad con `make sync` y workflows existentes.
# La fuente de verdad vive en protocolo/scripts/preflight.sh
exec bash "$(git rev-parse --show-toplevel)/protocolo/scripts/preflight.sh" "$@"
WRAPPER
    chmod +x scripts/preflight.sh
    echo
    echo "→ scripts/preflight.sh creado como wrapper"
fi

echo
echo "=== Instalación completa ==="
echo
echo "Próximos pasos:"
echo "  1. Verificar que el SessionStart hook está configurado (.claude/settings.json)"
echo "  2. Correr: bash protocolo/scripts/preflight.sh"
echo "  3. Leer protocolo/REGLAS.md para entender el protocolo completo"
