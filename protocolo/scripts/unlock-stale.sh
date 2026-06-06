#!/usr/bin/env bash
# unlock-stale.sh — detecta y libera locks LFS fantasma
#
# Un lock fantasma es un lock cuyo archivo NO tiene cambios pendientes
# (working tree y staged limpios vs HEAD). La sesión que lockeó ya
# terminó su trabajo y commiteó, pero olvidó hacer unlock.
#
# Política:
#   - Solo libera locks DEL usuario actual (no toca locks de otros).
#   - Solo libera locks cuyo archivo está limpio vs HEAD.
#   - Lista (sin tocar) locks de otros usuarios y locks con cambios.
#
# Uso:
#   bash scripts/unlock-stale.sh         # dry-run: lista qué libraría
#   bash scripts/unlock-stale.sh --apply # ejecuta el unlock
#
# Por qué existe: el protocolo dice "unlock al cerrar sesión", pero
# eso depende del juicio del AI. Cuando falla (sesión muere, olvido,
# crash), los locks quedan bloqueando trabajo de otras sesiones. Este
# script es la red de seguridad mecánica.

set -e
cd "$(git rev-parse --show-toplevel)"

APPLY=false
[[ "${1:-}" == "--apply" ]] && APPLY=true

LFS_USER=$(git config --get user.name 2>/dev/null || git config --get user.email 2>/dev/null)
if [[ -z "$LFS_USER" ]]; then
    echo "⚠️  No puedo determinar tu usuario git (user.name)."
    exit 1
fi

LOCKS=$(git lfs locks 2>/dev/null)
if [[ -z "$LOCKS" ]]; then
    echo "✓ No hay locks activos."
    exit 0
fi

GHOSTS=()
ACTIVE=()
OTHERS=()

while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    file=$(echo "$line" | awk '{print $1}')
    owner=$(echo "$line" | awk '{print $2}')

    # Lock de otro usuario: no tocar, solo reportar.
    if [[ "${owner,,}" != "${LFS_USER,,}" ]]; then
        OTHERS+=("$file ($owner)")
        continue
    fi

    # Mi lock: ¿el archivo tiene cambios?
    diff_count=$(git diff HEAD -- "$file" 2>/dev/null | wc -l | tr -d ' ')
    staged_count=$(git diff --cached -- "$file" 2>/dev/null | wc -l | tr -d ' ')

    if [[ "$diff_count" == "0" && "$staged_count" == "0" ]]; then
        GHOSTS+=("$file")
    else
        ACTIVE+=("$file (working: $diff_count líneas, staged: $staged_count)")
    fi
done <<< "$LOCKS"

echo "Análisis de locks LFS ($LFS_USER)"
echo "═══════════════════════════════════════"

if [[ ${#GHOSTS[@]} -gt 0 ]]; then
    echo ""
    echo "🟢 LOCKS FANTASMA (sin cambios — seguro de liberar):"
    for f in "${GHOSTS[@]}"; do echo "    $f"; done
fi

if [[ ${#ACTIVE[@]} -gt 0 ]]; then
    echo ""
    echo "🟡 LOCKS CON CAMBIOS (NO liberar — hay trabajo pendiente):"
    for f in "${ACTIVE[@]}"; do echo "    $f"; done
fi

if [[ ${#OTHERS[@]} -gt 0 ]]; then
    echo ""
    echo "🔵 LOCKS DE OTROS USUARIOS (fuera de scope):"
    for f in "${OTHERS[@]}"; do echo "    $f"; done
fi

if [[ ${#GHOSTS[@]} -eq 0 ]]; then
    echo ""
    echo "✓ No hay locks fantasma para liberar."
    exit 0
fi

echo ""
if [[ "$APPLY" == "true" ]]; then
    echo "Liberando ${#GHOSTS[@]} locks fantasma..."
    for f in "${GHOSTS[@]}"; do
        git lfs unlock --force "$f"
    done
    echo ""
    echo "✓ ${#GHOSTS[@]} locks fantasma liberados."
else
    echo "Dry-run. Para liberar: bash scripts/unlock-stale.sh --apply"
fi
